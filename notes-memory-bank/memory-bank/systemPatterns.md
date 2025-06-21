```markdown
# System Patterns (systemPatterns.md)

This document outlines the system patterns employed in the development of the AI-Powered Note Taking System, building upon the existing AI Chrome Chat Manager infrastructure. It details the architectural design, data models, API definitions, component structure, integration points, and scalability strategy.

## 1. Architectural Design: Microservices with Event-Driven Communication

The system adopts a microservices architecture to promote modularity, independent deployment, and scalability. Key services include:

*   **Note Service:** Manages the creation, retrieval, updating, and deletion (CRUD) of notes.
*   **User Service:** Handles user authentication, authorization, and profile management.
*   **AI Service:** Provides AI-powered features like summarization, topic extraction, sentiment analysis, and action item identification.  This leverages the existing AI Chrome Chat Manager infrastructure.
*   **Search Service:** Indexes and allows searching of notes.
*   **Collaboration Service:** Enables real-time collaborative editing of notes.

Communication between services is primarily asynchronous using an event-driven architecture with a message broker (e.g., RabbitMQ or Kafka). This decoupled approach enhances resilience and allows services to scale independently.  REST APIs are used for synchronous communication where necessary, primarily for initial setup and configuration.

**Diagram:**

```mermaid
graph LR
    A[User Interface] --> B(API Gateway);
    B --> C{Note Service};
    B --> D{User Service};
    B --> E{Search Service};
    B --> F{Collaboration Service};
    B --> G{AI Service};

    C -- Event Bus --> H{AI Service};
    C -- Event Bus --> I{Search Service};

    subgraph Microservices
        C; D; E; F; G;
    end

    subgraph Infrastructure
        H; I; Event Bus;
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
```

## 2. Data Models

The following are the core data models used in the system:

*   **User:**
    *   `userId` (UUID): Unique identifier for the user.
    *   `username` (String): User's username.
    *   `email` (String): User's email address.
    *   `passwordHash` (String): Hashed password.
    *   `creationDate` (Timestamp): Date the user account was created.
    *   `lastLogin` (Timestamp): Last login timestamp.

*   **Note:**
    *   `noteId` (UUID): Unique identifier for the note.
    *   `userId` (UUID): ID of the user who owns the note.
    *   `title` (String): Title of the note.
    *   `content` (String): Content of the note (Markdown format).
    *   `creationDate` (Timestamp): Date the note was created.
    *   `lastModified` (Timestamp): Date the note was last modified.
    *   `tags` (Array of Strings):  Tags associated with the note.
    *   `isPublic` (Boolean):  Indicates whether the note is publicly accessible.

*   **Tag:**
    *   `tagId` (UUID): Unique identifier for the tag.
    *   `tagName` (String): Name of the tag.
    *   `userId` (UUID): ID of the user who created the tag.

*   **AI Analysis Result:**
    *   `analysisId` (UUID): Unique identifier for the analysis result.
    *   `noteId` (UUID): ID of the note the analysis is for.
    *   `summary` (String): Summarized content of the note.
    *   `topics` (Array of Strings): Extracted topics from the note.
    *   `sentiment` (String): Sentiment analysis result (e.g., Positive, Negative, Neutral).
    *   `actionItems` (Array of Strings):  Identified action items from the note.
    *   `analysisDate` (Timestamp): Date the analysis was performed.

## 3. API Definitions

The system exposes REST APIs for interaction with each microservice. Example API endpoints:

*   **Note Service:**
    *   `POST /notes`: Create a new note.
    *   `GET /notes/{noteId}`: Get a note by ID.
    *   `PUT /notes/{noteId}`: Update a note.
    *   `DELETE /notes/{noteId}`: Delete a note.
    *   `GET /notes?userId={userId}`:  Get all notes for a user.

*   **User Service:**
    *   `POST /users/register`: Register a new user.
    *   `POST /users/login`: Log in a user.
    *   `GET /users/{userId}`: Get user information.
    *   `PUT /users/{userId}`: Update user information.

*   **AI Service:**
    *   `POST /ai/analyze`: Analyze a note (requires `noteId` in request body).  Returns `analysisId`.
    *   `GET /ai/results/{analysisId}`: Get AI analysis results by ID.

These APIs will use standard HTTP status codes (200, 201, 400, 401, 404, 500) and JSON for request/response bodies. Authentication will be handled using JWT (JSON Web Tokens).

## 4. Component Structure

Each microservice will have a similar component structure:

*   **API Layer:** Exposes REST endpoints and handles request/response processing.
*   **Business Logic Layer:** Implements the core business logic for the service.
*   **Data Access Layer:** Interacts with the database to persist and retrieve data.
*   **Event Publisher:**  Publishes events to the message broker.
*   **Event Consumer:** Consumes events from the message broker.

This layered architecture promotes separation of concerns and testability.

## 5. Integration Points

*   **AI Chrome Chat Manager:**  The AI Service directly integrates with the existing AI Chrome Chat Manager infrastructure.  This infrastructure provides the core AI processing capabilities, allowing the Note Taking System to leverage existing AI models and algorithms.  The integration primarily involves sending note content to the AI Chrome Chat Manager for analysis and receiving the results (summary, topics, sentiment, action items). This may involve a new API endpoint within the AI Chrome Chat Manager, specifically designed for this integration.
*   **Message Broker (RabbitMQ/Kafka):** Used for asynchronous communication between services.
*   **Database (PostgreSQL/MongoDB):** Used for persistent storage of data. Each service will likely have its own database instance to ensure data isolation.
*   **API Gateway:** Acts as a single entry point for all API requests and handles authentication, authorization, and routing.
*   **Search Index (Elasticsearch/Solr):**  Used by the Search Service to index and search notes.

## 6. Scalability Strategy

The system is designed for horizontal scalability.

*   **Microservices:** Each microservice can be scaled independently based on its resource requirements.
*   **Load Balancing:**  The API Gateway will distribute traffic across multiple instances of each microservice.
*   **Database Sharding:**  Database sharding can be implemented to distribute data across multiple database servers.
*   **Caching:**  Caching can be used to reduce database load and improve performance.  Redis or Memcached can be used for caching frequently accessed data.
*   **Message Broker Scaling:**  The message broker can be scaled horizontally to handle increased event traffic.

The event-driven architecture allows for asynchronous processing, which further enhances scalability and resilience. We will leverage cloud-based infrastructure (e.g., AWS, Azure, GCP) to facilitate automated scaling and resource management.

Created on 21.06.2025
```