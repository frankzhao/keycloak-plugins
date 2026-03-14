# Stage 1 — Build the provider JAR
FROM maven:3.9-eclipse-temurin-17 AS builder

WORKDIR /build
COPY pom.xml .
RUN mvn dependency:go-offline -q
COPY src/ ./src/
RUN mvn package -q -DskipTests

# Stage 2 — Keycloak 24 with the provider installed
FROM quay.io/keycloak/keycloak:24.0

COPY --from=builder /build/target/keycloak-custom-idp-mapper.jar /opt/keycloak/providers/
