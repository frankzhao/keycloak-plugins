# Stage 1 — Build the provider JAR
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build
COPY pom.xml .
# Download dependencies first for better layer caching
RUN mvn dependency:go-offline -q
COPY src/ ./src/
RUN mvn package -q -DskipTests

# Stage 2 — Keycloak 24 with the provider installed
FROM quay.io/keycloak/keycloak:24.0

# Copy the compiled provider JAR into Keycloak's providers directory
COPY --from=builder /build/target/keycloak-custom-login.jar /opt/keycloak/providers/

# In start-dev mode Keycloak auto-discovers providers; no explicit build step needed.
