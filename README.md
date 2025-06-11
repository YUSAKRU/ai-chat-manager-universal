# AI Chrome Chat Manager

AI Chrome Chat Manager is a Python project that facilitates communication between two Chrome windows acting as AI chat interfaces. One window serves as a Project Manager while the other acts as a Lead Developer. Additionally, a third party, referred to as the Boss, can join the conversation at any time.

## Project Structure

```
ai-chrome-chat-manager
├── src
│   ├── main.py
│   ├── browser_handler.py
│   ├── message_broker.py
│   └── roles
│       ├── __init__.py
│       ├── project_manager.py
│       ├── lead_developer.py
│       └── boss.py
├── requirements.txt
└── README.md
```

## Installation

To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd ai-chrome-chat-manager
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

1. Run the main application:
   ```
   python src/main.py
   ```

2. The application will open two Chrome windows for the Project Manager and Lead Developer. You can interact with them through the defined methods.

## Features

- **Project Manager Role**: Assign tasks and provide feedback.
- **Lead Developer Role**: Implement features and report progress.
- **Boss Role**: Join the conversation and review progress at any time.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.