package com.example.userservice.service;

import com.example.userservice.model.User;
import com.example.userservice.web.dto.UserDto;

import java.util.List;

public interface UserService {
    User getUserById(Long id);
    User getUserByUsername(String username);
    List<User> getAllUsers();
    User createUser(UserDto userDto);
    User updateUser(Long id, UserDto userDto);
    void deleteUser(Long id);
    User updateAvatar(Long id, String avatarUrl);
}
