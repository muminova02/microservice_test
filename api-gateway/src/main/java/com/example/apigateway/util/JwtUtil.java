package com.example.apigateway.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.security.Key;
import java.util.Date;
import java.util.function.Function;
import java.util.function.Supplier;

@Component
public class JwtUtil {

    private static final Logger logger = LoggerFactory.getLogger(JwtUtil.class);

    @Value("${jwt.secret}")
    private String secret;

    @Autowired
    private Tracer tracer;

    private <T> T executeWithTracing(String operationName, Function<Span, T> operation) {
        Span span = tracer.nextSpan()
                .name(operationName)
                .tag("component", "jwt-util")
                .start();

        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            return operation.apply(span);
        } finally {
            span.end();
        }
    }

    private void executeWithTracingVoid(String operationName, java.util.function.Consumer<Span> operation) {
        Span span = tracer.nextSpan()
                .name(operationName)
                .tag("component", "jwt-util")
                .start();

        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            operation.accept(span);
        } finally {
            span.end();
        }
    }

    public void validateToken(String token) {
        executeWithTracingVoid("jwt-validation", span -> {
            logger.debug("Validating JWT token");

            try {
                Jwts.parserBuilder()
                        .setSigningKey(getSigningKey())
                        .build()
                        .parseClaimsJws(token);

                span.tag("jwt.validation.result", "success");
                logger.debug("JWT token validation successful");

            } catch (JwtException e) {
                span.tag("jwt.validation.result", "failed");
                span.tag("error", e.getMessage());
                logger.error("JWT token validation failed: {}", e.getMessage());
                throw new RuntimeException("Invalid JWT token: " + e.getMessage());
            }
        });
    }

    public String extractUsername(String token) {
        return executeWithTracing("jwt-extract-username", span -> {
            logger.debug("Extracting username from JWT token");

            try {
                String username = extractAllClaims(token).getSubject();

                span.tag("jwt.username.extracted", username != null ? "true" : "false");
                if (username != null) {
                    span.tag("jwt.username", username);
                }

                logger.debug("Username extracted: {}", username);
                return username;

            } catch (Exception e) {
                span.tag("error", e.getMessage());
                logger.error("Error extracting username from JWT: {}", e.getMessage());
                throw e;
            }
        });
    }

    private Claims extractAllClaims(String token) {
        return executeWithTracing("jwt-extract-claims", span -> {
            try {
                Claims claims = Jwts.parserBuilder()
                        .setSigningKey(getSigningKey())
                        .build()
                        .parseClaimsJws(token)
                        .getBody();

                span.tag("jwt.claims.extracted", "true");
                span.tag("jwt.subject", claims.getSubject());

                if (claims.getExpiration() != null) {
                    span.tag("jwt.expiration", claims.getExpiration().toString());
                }

                return claims;

            } catch (Exception e) {
                span.tag("error", e.getMessage());
                logger.error("Error extracting claims from JWT: {}", e.getMessage());
                throw e;
            }
        });
    }

    private Key getSigningKey() {
        byte[] keyBytes = secret.getBytes(StandardCharsets.UTF_8);
        return Keys.hmacShaKeyFor(keyBytes);
    }
}