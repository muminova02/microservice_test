package com.example.apigateway.filter;

import com.example.apigateway.util.JwtUtil;
import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.gateway.filter.GatewayFilter;
import org.springframework.cloud.gateway.filter.factory.AbstractGatewayFilterFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.http.server.reactive.ServerHttpResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
public class JwtAuthenticationFilter extends AbstractGatewayFilterFactory<JwtAuthenticationFilter.Config> {

    private static final Logger logger = LoggerFactory.getLogger(JwtAuthenticationFilter.class);

    @Autowired
    private JwtUtil jwtUtil;

    @Autowired
    private Tracer tracer;

    public JwtAuthenticationFilter() {
        super(Config.class);
    }

    @Override
    public GatewayFilter apply(Config config) {
        return (exchange, chain) -> {
            ServerHttpRequest request = exchange.getRequest();

            // Create tracing span for JWT authentication
            Span span = tracer.nextSpan()
                    .name("jwt-authentication")
                    .tag("http.method", request.getMethod().toString())
                    .tag("http.url", request.getURI().toString())
                    .tag("component", "jwt-filter")
                    .start();

            try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
                // Skip JWT check for authentication paths
                if (request.getURI().getPath().contains("/auth/")) {
                    span.tag("auth.skip", "true");
                    span.tag("auth.reason", "auth-endpoint");
                    logger.info("Skipping JWT validation for auth endpoint: {}", request.getURI().getPath());
                    return chain.filter(exchange)
                            .doFinally(signalType -> span.end());
                }

                span.tag("auth.skip", "false");

                if (!request.getHeaders().containsKey(HttpHeaders.AUTHORIZATION)) {
                    span.tag("auth.result", "missing-header");
                    span.tag("error", "No Authorization header");
                    logger.warn("Missing Authorization header for request: {}", request.getURI().getPath());
                    return onError(exchange, "No Authorization header", HttpStatus.UNAUTHORIZED, span);
                }

                String authHeader = request.getHeaders().getFirst(HttpHeaders.AUTHORIZATION);
                if (authHeader == null || !authHeader.startsWith("Bearer ")) {
                    span.tag("auth.result", "invalid-header-format");
                    span.tag("error", "Invalid Authorization header format");
                    logger.warn("Invalid Authorization header format for request: {}", request.getURI().getPath());
                    return onError(exchange, "Invalid Authorization header format", HttpStatus.UNAUTHORIZED, span);
                }

                String token = authHeader.substring(7);
                span.tag("auth.token.present", "true");

                try {
                    jwtUtil.validateToken(token);
                    String username = jwtUtil.extractUsername(token);

                    span.tag("auth.result", "success");
                    span.tag("auth.user", username);

                    logger.info("JWT validation successful for user: {} on path: {}", username, request.getURI().getPath());

                    // Add user info from JWT to headers for downstream services
                    ServerHttpRequest modifiedRequest = request.mutate()
                            .header("X-Auth-User", username)
                            .header("X-Trace-Id", span.context().traceId())
                            .header("X-Span-Id", span.context().spanId())
                            .build();

                    return chain.filter(exchange.mutate().request(modifiedRequest).build())
                            .doOnSuccess(unused -> {
                                span.tag("auth.downstream.result", "success");
                                logger.debug("Downstream request successful for user: {}", username);
                            })
                            .doOnError(error -> {
                                span.tag("auth.downstream.result", "error");
                                span.tag("downstream.error", error.getMessage());
                                logger.error("Downstream request failed for user: {} - Error: {}", username, error.getMessage());
                            })
                            .doFinally(signalType -> span.end());

                } catch (Exception e) {
                    span.tag("auth.result", "token-validation-failed");
                    span.tag("error", e.getMessage());
                    logger.error("JWT validation failed for request: {} - Error: {}",
                            request.getURI().getPath(), e.getMessage());
                    return onError(exchange, "Invalid JWT token: " + e.getMessage(), HttpStatus.UNAUTHORIZED, span);
                }
            }
        };
    }

    private Mono<Void> onError(ServerWebExchange exchange, String error, HttpStatus httpStatus, Span span) {
        ServerHttpResponse response = exchange.getResponse();
        response.setStatusCode(httpStatus);

        // Add final tags before ending span
        span.tag("http.status_code", httpStatus.toString());
        span.tag("auth.final.result", "error");

        // Log error with trace context
        logger.error("Authentication error: {} for request: {}",
                error, exchange.getRequest().getURI().getPath());

        return response.setComplete()
                .doFinally(signalType -> span.end());
    }

    public static class Config {
        // Configuration properties can be added here
    }
}