package com.example.userservice.service;

import com.example.userservice.model.User;
import com.example.userservice.repository.UserRepository;
import com.example.userservice.service.UserService;
import com.example.userservice.web.dto.UserDto;
import io.micrometer.tracing.Span;
import io.micrometer.tracing.Tracer;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.function.Function;

@Service
public class UserServiceImpl implements UserService {

    private static final Logger logger = LoggerFactory.getLogger(UserServiceImpl.class);

    private final UserRepository userRepository;
    private final Tracer tracer;

    @Autowired
    public UserServiceImpl(UserRepository userRepository, Tracer tracer) {
        this.userRepository = userRepository;
        this.tracer = tracer;
    }

    private <T> T executeWithTracing(String operationName, Function<Span, T> operation) {
        Span span = tracer.nextSpan()
                .name(operationName)
                .tag("service", "user-service")
                .start();

        try (Tracer.SpanInScope ws = tracer.withSpan(span)) {
            return operation.apply(span);
        } finally {
            span.end();
        }
    }

    @Override
    public User getUserById(Long id) {
        return executeWithTracing("get-user-by-id", span -> {
            span.tag("user.id", id.toString());
            logger.info("Getting user by ID: {}", id);

            User user = userRepository.findById(id)
                    .orElseThrow(() -> {
                        span.tag("error", "User not found");
                        logger.warn("User not found with id: {}", id);
                        return new RuntimeException("User not found with id: " + id);
                    });

            span.tag("user.username", user.getUsername());
            span.tag("user.email", user.getEmail());
            logger.info("User found: {}", user.getUsername());

            return user;
        });
    }

    @Override
    public User getUserByUsername(String username) {
        return executeWithTracing("get-user-by-username", span -> {
            span.tag("user.username", username);
            logger.info("Getting user by username: {}", username);

            User user = userRepository.findByUsername(username)
                    .orElseThrow(() -> {
                        span.tag("error", "User not found");
                        logger.warn("User not found with username: {}", username);
                        return new RuntimeException("User not found with username: " + username);
                    });

            span.tag("user.id", user.getId().toString());
            span.tag("user.email", user.getEmail());
            logger.info("User found by username: {}", username);

            return user;
        });
    }

    @Override
    public List<User> getAllUsers() {
        return executeWithTracing("get-all-users", span -> {
            logger.info("Getting all users");

            List<User> users = userRepository.findAll();

            span.tag("users.count", String.valueOf(users.size()));
            logger.info("Found {} users", users.size());

            return users;
        });
    }

    @Override
    public User createUser(UserDto userDto) {
        return executeWithTracing("create-user", span -> {
            span.tag("user.username", userDto.getUsername());
            span.tag("user.email", userDto.getEmail());
            logger.info("Creating new user: {}", userDto.getUsername());

            // Check if user already exists
            if (userRepository.findByUsername(userDto.getUsername()).isPresent()) {
                span.tag("error", "Username already exists");
                logger.warn("Username already exists: {}", userDto.getUsername());
                throw new RuntimeException("Username already exists: " + userDto.getUsername());
            }

            if (userRepository.findByEmail(userDto.getEmail()).isPresent()) {
                span.tag("error", "Email already exists");
                logger.warn("Email already exists: {}", userDto.getEmail());
                throw new RuntimeException("Email already exists: " + userDto.getEmail());
            }

            User user = new User();
            user.setUsername(userDto.getUsername());
            user.setEmail(userDto.getEmail());
            user.setFullName(userDto.getFullName());
            user.setBio(userDto.getBio());

            User savedUser = userRepository.save(user);

            span.tag("user.id", savedUser.getId().toString());
            span.tag("operation.result", "success");
            logger.info("User created successfully: {} with ID: {}",
                    savedUser.getUsername(), savedUser.getId());

            return savedUser;
        });
    }

    @Override
    public User updateUser(Long id, UserDto userDto) {
        return executeWithTracing("update-user", span -> {
            span.tag("user.id", id.toString());
            logger.info("Updating user with ID: {}", id);

            User existingUser = getUserById(id);
            span.tag("user.username", existingUser.getUsername());

            if (userDto.getUsername() != null) {
                existingUser.setUsername(userDto.getUsername());
            }

            if (userDto.getEmail() != null) {
                existingUser.setEmail(userDto.getEmail());
            }

            if (userDto.getFullName() != null) {
                existingUser.setFullName(userDto.getFullName());
            }

            if (userDto.getBio() != null) {
                existingUser.setBio(userDto.getBio());
            }

            User updatedUser = userRepository.save(existingUser);

            span.tag("operation.result", "success");
            logger.info("User updated successfully: {}", updatedUser.getUsername());

            return updatedUser;
        });
    }

    @Override
    public void deleteUser(Long id) {
        executeWithTracing("delete-user", span -> {
            span.tag("user.id", id.toString());
            logger.info("Deleting user with ID: {}", id);

            User user = getUserById(id);
            span.tag("user.username", user.getUsername());

            userRepository.delete(user);

            span.tag("operation.result", "success");
            logger.info("User deleted successfully: {}", user.getUsername());

            return null; // Void operations return null
        });
    }

    @Override
    public User updateAvatar(Long id, String avatarUrl) {
        return executeWithTracing("update-user-avatar", span -> {
            span.tag("user.id", id.toString());
            logger.info("Updating avatar for user with ID: {}", id);

            User user = getUserById(id);
            span.tag("user.username", user.getUsername());

            user.setAvatarUrl(avatarUrl);
            User updatedUser = userRepository.save(user);

            span.tag("operation.result", "success");
            logger.info("Avatar updated successfully for user: {}", user.getUsername());

            return updatedUser;
        });
    }
}