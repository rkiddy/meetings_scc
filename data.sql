-- MySQL dump 10.13  Distrib 8.0.32, for Linux (x86_64)
--
-- Host: localhost    Database: ca_scc_meetings
-- ------------------------------------------------------
-- Server version	8.0.32-0ubuntu0.22.04.2

--
-- Table structure for table `meetings`
--

DROP TABLE IF EXISTS `meetings`;
CREATE TABLE `meetings` (
  `pk` int NOT NULL,
  `full_name` varchar(255) DEFAULT NULL,
  `mtg_name` varchar(255) DEFAULT NULL,
  `sub_name` varchar(255) DEFAULT NULL,
  `mtg_time` varchar(31) DEFAULT NULL,
  `scp_time` varchar(63) DEFAULT NULL,
  `status` varchar(31) DEFAULT NULL,
  `created` bigint DEFAULT NULL,
  `updated` bigint DEFAULT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `notifications`
--

DROP TABLE IF EXISTS `notifications`;
CREATE TABLE `notifications` (
  `pk` int NOT NULL,
  `meeting_pk` int DEFAULT NULL,
  `created` bigint DEFAULT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `notify_requests`
--

DROP TABLE IF EXISTS `notify_requests`;
CREATE TABLE `notify_requests` (
  `pk` int NOT NULL,
  `user_pk` int DEFAULT NULL,
  `request_info` varchar(127) DEFAULT NULL,
  `created` bigint DEFAULT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `notify_users_join`
--

DROP TABLE IF EXISTS `notify_users_join`;
CREATE TABLE `notify_users_join` (
  `meeting_pk` int DEFAULT NULL,
  `user_pk` int DEFAULT NULL,
  `notified` bigint DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `resources`
--

DROP TABLE IF EXISTS `resources`;
CREATE TABLE `resources` (
  `pk` int NOT NULL,
  `meeting_pk` int DEFAULT NULL,
  `name` varchar(63) DEFAULT NULL,
  `url` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `pk` int NOT NULL,
  `email` varchar(63) DEFAULT NULL,
  `name` varchar(63) DEFAULT NULL,
  `created` bigint DEFAULT NULL,
  `deleted` bigint DEFAULT NULL,
  PRIMARY KEY (`pk`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Dump completed on 2023-03-30 10:37:02
