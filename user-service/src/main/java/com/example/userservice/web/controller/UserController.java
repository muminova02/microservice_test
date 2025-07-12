package com.example.userservice.web.controller;

import com.example.userservice.model.User;
import com.example.userservice.service.UserService;
import com.example.userservice.web.dto.UserDto;
import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.function.Function;

@RestController
@RequestMapping("/users")
@Tag(name = "User Management", description = "APIs for managing user profiles")
public class UserController {

    private static final Logger logger = LoggerFactory.getLogger(UserController.class);

    private final UserService userService;
    private final Tracer tracer;

    @Autowired
    public UserController(UserService userService, Tracer tracer) {
        this.userService = userService;
        this.tracer = tracer;
    }

    private <T> T executeWithTracing(String operationName, String endpoint, Function<Span, T> operation) {
        Span span = tracer.nextSpan()
                .name(operationName)
                .tag("service", "user-service")
                .tag("endpoint", endpoint)
                .start();

        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            return operation.apply(span);
        } finally {
            span.end();
        }
    }

    @Operation(
            summary = "Get user health check",
            description = "Returns health status of user service"
    )
    @ApiResponses(value = {
            @ApiResponse(
                    responseCode = "200",
                    description = "Service is healthy",
                    content = @Content(
                            mediaType = "application/json",
                            schema = @Schema(implementation = Map.class)
                    )
            )
    })
    @GetMapping("/health")
    public ResponseEntity<Map<String, Object>> health() {
        return executeWithTracing("health-check", "/users/health", span -> {
            logger.info("Health check requested");

            Map<String, Object> response = new HashMap<>();
            response.put("status", "UP");
            response.put("service", "user-service");
            response.put("timestamp", System.currentTimeMillis());

            span.tag("health.status", "UP");
            return ResponseEntity.ok(response);
        });
    }

    @GetMapping
    @Operation(summary = "Get all users", description = "Retrieve all users from the system")
    public ResponseEntity<List<User>> getAllUsers(
            @RequestHeader(value = "X-Auth-User", required = false) String authUser) {

        return executeWithTracing("get-all-users-endpoint", "/users", span -> {
            if (authUser != null) {
                span.tag("auth.user", authUser);
                logger.info("Get all users requested by: {}", authUser);
            } else {
                logger.info("Get all users requested");
            }

            List<User> users = userService.getAllUsers();

            span.tag("users.count", String.valueOf(users.size()));
            logger.info("Returning {} users", users.size());

            return ResponseEntity.ok(users);
        });
    }

    @GetMapping("/{id}")
    @Operation(summary = "Get user by ID", description = "Retrieve a specific user by their ID")
    public ResponseEntity<User> getUserById(@PathVariable Long id,
                                            @RequestHeader(value = "X-Auth-User", required = false) String authUser) {

        return executeWithTracing("get-user-by-id-endpoint", "/users/{id}", span -> {
            span.tag("user.id", id.toString());

            if (authUser != null) {
                span.tag("auth.user", authUser);
                logger.info("Get user by ID: {} requested by: {}", id, authUser);
            } else {
                logger.info("Get user by ID: {} requested", id);
            }

            User user = userService.getUserById(id);

            span.tag("user.username", user.getUsername());
            logger.info("Returning user: {}", user.getUsername());

            return ResponseEntity.ok(user);
        });
    }

    @GetMapping("/username/{username}")
    @Operation(summary = "Get user by username", description = "Retrieve a specific user by their username")
    public ResponseEntity<User> getUserByUsername(@PathVariable String username,
                                                  @RequestHeader(value = "X-Auth-User", required = false) String authUser) {

        return executeWithTracing("get-user-by-username-endpoint", "/users/username/{username}", span -> {
            span.tag("user.username", username);

            if (authUser != null) {
                span.tag("auth.user", authUser);
                logger.info("Get user by username: {} requested by: {}", username, authUser);
            } else {
                logger.info("Get user by username: {} requested", username);
            }

            User user = userService.getUserByUsername(username);

            span.tag("user.id", user.getId().toString());
            logger.info("Returning user: {} with ID: {}", username, user.getId());

            return ResponseEntity.ok(user);
        });
    }

    @PostMapping
    @Operation(summary = "Create new user", description = "Create a new user in the system")
    public ResponseEntity<User> createUser(@RequestBody UserDto userDto,
                                           @RequestHeader(value = "X-Auth-User", required = false) String authUser) {

        return executeWithTracing("create-user-endpoint", "/users", span -> {
            span.tag("user.username", userDto.getUsername());

            if (authUser != null) {
                span.tag("auth.user", authUser);
                logger.info("Create user: {} requested by: {}", userDto.getUsername(), authUser);
            } else {
                logger.info("Create user: {} requested", userDto.getUsername());
            }

            User createdUser = userService.createUser(userDto);

            span.tag("user.id", createdUser.getId().toString());
            span.tag("operation.result", "success");
            logger.info("User created: {} with ID: {}", createdUser.getUsername(), createdUser.getId());

            return new ResponseEntity<>(createdUser, HttpStatus.CREATED);
        });
    }

    @PutMapping("/{id}")
    @Operation(summary = "Update user", description = "Update an existing user")
    public ResponseEntity<User> updateUser(@PathVariable Long id, @RequestBody UserDto userDto,
                                           @RequestHeader(value = "X-Auth-User", required = false) String authUser) {

        return executeWithTracing("update-user-endpoint", "/users/{id}", span -> {
            span.tag("user.id", id.toString());

            if (authUser != null) {
                span.tag("auth.user", authUser);
                logger.info("Update user ID: {} requested by: {}", id, authUser);
            } else {
                logger.info("Update user ID: {} requested", id);
            }

            User updatedUser = userService.updateUser(id, userDto);

            span.tag("user.username", updatedUser.getUsername());
            span.tag("operation.result", "success");
            logger.info("User updated: {}", updatedUser.getUsername());

            return ResponseEntity.ok(updatedUser);
        });
    }

    @DeleteMapping("/{id}")
    @Operation(summary = "Delete user", description = "Delete a user from the system")
    public ResponseEntity<Void> deleteUser(@PathVariable Long id,
                                           @RequestHeader(value = "X-Auth-User", required = false) String authUser) {

        return executeWithTracing("delete-user-endpoint", "/users/{id}", span -> {
            span.tag("user.id", id.toString());

            if (authUser != null) {
                span.tag("auth.user", authUser);
                logger.info("Delete user ID: {} requested by: {}", id, authUser);
            } else {
                logger.info("Delete user ID: {} requested", id);
            }

            userService.deleteUser(id);

            span.tag("operation.result", "success");
            logger.info("User deleted with ID: {}", id);

            return ResponseEntity.noContent().build();
        });
    }

    @PutMapping("/{id}/avatar")
    @Operation(summary = "Update user avatar", description = "Update a user's avatar URL")
    public ResponseEntity<User> updateAvatar(@PathVariable Long id, @RequestParam String avatarUrl,
                                             @RequestHeader(value = "X-Auth-User", required = false) String authUser) {

        return executeWithTracing("update-avatar-endpoint", "/users/{id}/avatar", span -> {
            span.tag("user.id", id.toString());

            if (authUser != null) {
                span.tag("auth.user", authUser);
                logger.info("Update avatar for user ID: {} requested by: {}", id, authUser);
            } else {
                logger.info("Update avatar for user ID: {} requested", id);
            }

            User updatedUser = userService.updateAvatar(id, avatarUrl);

            span.tag("user.username", updatedUser.getUsername());
            span.tag("operation.result", "success");
            logger.info("Avatar updated for user: {}", updatedUser.getUsername());

            return ResponseEntity.ok(updatedUser);
        });
    }
}