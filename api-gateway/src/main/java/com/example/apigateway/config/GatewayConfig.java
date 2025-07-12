package com.example.apigateway.config;

import com.example.apigateway.filter.JwtAuthenticationFilter;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GatewayConfig {

    private static final Logger logger = LoggerFactory.getLogger(GatewayConfig.class);

    @Autowired
    private JwtAuthenticationFilter filter;

    @Bean
    public RouteLocator routes(RouteLocatorBuilder builder) {
        logger.info("Configuring Gateway routes with JWT authentication");

        return builder.routes()
                .route("auth-service", r -> r.path("/auth/**")
                        .filters(f -> f.addRequestHeader("X-Gateway-Source", "api-gateway"))
                        .uri("http://localhost:8000"))
                .route("user-service", r -> r.path("/users/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config()))
                                .addRequestHeader("X-Gateway-Source", "api-gateway"))
                        .uri("lb://USER-SERVICE"))
                .route("post-service", r -> r.path("/posts/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config()))
                                .addRequestHeader("X-Gateway-Source", "api-gateway"))
                        .uri("lb://POST-SERVICE"))
                .route("admin-service", r -> r.path("/admin/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config()))
                                .addRequestHeader("X-Gateway-Source", "api-gateway"))
                        .uri("lb://ADMIN-SERVICE"))
                .route("target-service", r -> r.path("/targets/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config()))
                                .addRequestHeader("X-Gateway-Source", "api-gateway"))
                        .uri("lb://TARGET-SERVICE"))
                .build();
    }
}