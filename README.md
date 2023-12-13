# DreamGenie
## Overview
Dream Genie is an innovative application designed to enable users, especially older adults, to experience their dreams in a new light. It allows users to talk about a dream, then identifies key scenes and creates artistic representations of each scene.

## Demo
Click the video to watch on youtube:
<div align="center">
  <a href="https://www.youtube.com/watch?v=vYGtx706kPA">
    <img src="https://github.com/BDT2023/DreamGenie/assets/72495653/14f8b273-cad0-47b0-9920-8a922551fd08" alt="Watch the video" style="width:100%;">
  </a>
</div>

![Dragon and a person flying towards a glowing island](https://github.com/BDT2023/DreamGenie/assets/92650578/625c419a-2263-4b21-a902-2c5a1415e001)

## Features
- Voice/text input for dream scene generation.
- GPT-3 for splitting transcribed text into individual dream scenes.
- Image generation using Stable Diffusion.
- Flask-based web application for user interaction.
- MongoDB for data storage and feedback collection.

## Getting Started

## System Architecture and Deployment

Dream Genie is hosted on Microsoft Azure, leveraging Docker Compose for efficient server management. The deployment includes:

- **Gunicorn Container:** Handles application logic and incoming requests.
- **Redis Container:** Manages user session data.
- **Nginx Container:** Provides load balancing for high availability.

Additionally, the project employs localized servers with GPU support for computationally intensive tasks, such as running the Stable Diffusion and Whisper models.

### Stable Diffusion and Whisper Services

- **Stable Diffusion:** This image generation model is used to create visual representations of dream scenes. It's hosted locally on our servers, accessed through Ngrok tunnels for security.
- **Whisper:** An open-source speech recognition model, Whisper is employed for transcribing user input and is similarly hosted on local servers.

For a detailed exploration of Dream Genie's architecture, deployment strategies, and technologies, please refer to our System Architecture Document [(SAD)](Dream_Genie_SAD.pdf).

### Prerequisites
- Python 3.9+.
- Redis Server for caching and background tasks.

### Installation
1. Clone the repository:
   ```
   git clone https://github.com/BDT2023/DreamGenie.git
   ```
2. Navigate to the project directory and install dependencies using the provided `requirements.txt` files.

### Usage
Follow the instructions in the application for providing dream inputs and viewing generated scenes.

## License
This project is licensed under MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments
- Special thanks to all contributors and supporters of the Dream Genie project.
- Appreciation to the open-source community for various tools and libraries used in this project.

## Contact
For any queries, please contact:
- Ben Eli [@beneli1](https://www.github.com/beneli1)
- Daniel Bronfman [@funkey7dan](https://www.github.com/funkey7dan)
- Tomer Pardilov [@TomerPardi](https://www.github.com/TomerPardi)
