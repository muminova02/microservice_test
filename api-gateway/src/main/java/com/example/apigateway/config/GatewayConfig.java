package com.example.apigateway.config;

import com.example.apigateway.filter.JwtAuthenticationFilter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cloud.gateway.route.RouteLocator;
import org.springframework.cloud.gateway.route.builder.RouteLocatorBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class GatewayConfig {

    @Autowired
    private JwtAuthenticationFilter filter;

    @Bean
    public RouteLocator routes(RouteLocatorBuilder builder) {
        return builder.routes()
                .route("auth-service", r -> r.path("/auth/**")
                        .uri("lb://AUTH-SERVICE"))
                .route("user-service", r -> r.path("/users/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config())))
                        .uri("lb://USER-SERVICE"))
                .route("post-service", r -> r.path("/posts/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config())))
                        .uri("lb://POST-SERVICE"))
                .route("admin-service", r -> r.path("/admin/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config())))
                        .uri("lb://ADMIN-SERVICE"))
                .route("target-service", r -> r.path("/targets/**")
                        .filters(f -> f.filter(filter.apply(new JwtAuthenticationFilter.Config())))
                        .uri("lb://TARGET-SERVICE"))
                .build();
    }
}
