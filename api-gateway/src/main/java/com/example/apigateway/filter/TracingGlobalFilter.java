package com.example.apigateway.filter;

import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.annotation.Order;
import org.springframework.http.server.reactive.ServerHttpRequest;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

@Component
@Order(-1)
public class TracingGlobalFilter implements GlobalFilter {

    private static final Logger logger = LoggerFactory.getLogger(TracingGlobalFilter.class);

    @Autowired
    private Tracer tracer;

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        ServerHttpRequest request = exchange.getRequest();

        Span span = tracer.nextSpan()
                .name("api-gateway-request")
                .tag("http.method", request.getMethod().toString())
                .tag("http.url", request.getURI().toString())
                .tag("http.path", request.getPath().value())
                .tag("component", "api-gateway")
                .start();

        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            logger.info("API Gateway processing request: {} {}",
                    request.getMethod(), request.getURI());

            return chain.filter(exchange)
                    .doOnSuccess(unused -> {
                        // Success callback
                        if (exchange.getResponse().getStatusCode() != null) {
                            span.tag("http.status_code",
                                    exchange.getResponse().getStatusCode().toString());
                        }

                        logger.info("API Gateway response: {} for {} {}",
                                exchange.getResponse().getStatusCode(),
                                request.getMethod(),
                                request.getURI());
                    })
                    .doOnError(error -> {
                        // Error callback
                        span.tag("error", error.getMessage());
                        span.tag("http.status_code", "500");

                        logger.error("API Gateway error processing request: {} {} - {}",
                                request.getMethod(),
                                request.getURI(),
                                error.getMessage());
                    })
                    .doFinally(signalType -> {
                        // Always executed - cleanup
                        span.end();
                    });
        }
    }
}