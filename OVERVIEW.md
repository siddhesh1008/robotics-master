# What is this?

I'm building a system where one mini computer acts as the brain for a bunch of robots. Instead of each robot being its own isolated project, they all connect back to a central master that coordinates everything.

Think of it like a smart home hub, but for robots.

## The big picture

​```mermaid
flowchart TB
    User([You<br/>typing or talking])
    Master[Mini PC<br/>The Brain]
    LLM[AI Model<br/>Understands you]
    Rover[Rover<br/>drives around]
    Arm[Robotic Arm<br/>picks things up]
    Bot[Companion Bot<br/>interacts with you]

    User --> Master
    Master <--> LLM
    Master --> Rover
    Master --> Arm
    Master --> Bot
​```

## Why bother?

Right now each robot lives in its own world. The robotic arm doesn't know the rover exists. One robot can't tell another to do something. By giving them a shared brain, they can work together and be controlled from one place, even from a phone.

## How a command actually flows

​```mermaid
flowchart LR
    A[Say: move rover forward 2 meters]
    B[Brain receives it]
    C[AI translates it into robot language]
    D[Brain sends structured command]
    E[Rover does the thing]

    A --> B --> C --> D --> E
​```

Behind the scenes the AI converts plain English into something like:

​```json
{
  "robot": "rover",
  "action": "move",
  "parameters": { "distance": 2, "unit": "meters" }
}
​```

Robots cannot understand "move forward a bit." They need exact numbers. The AI is the translator.

## The robots (examples)

​```mermaid
flowchart TD
    Rover[Rover<br/>Wheeled robot with sensors]
    Arm[Robotic Arm<br/>Multi-joint, picks and places]
    Bot[Companion Bot<br/>Animated, talks and listens]
​```

Each is a separate project on different hardware. Some run on tiny microcontrollers, some on full Linux computers. The master is what makes them feel like one system.

## What the master can do today

- Understand commands written in normal English
- Convert them into structured robot instructions using a local AI model (no internet needed)
- Send commands across the home network to any connected robot
- Be reached from a phone anywhere in the world, privately, through a secure tunnel

## What's next

- Hook up the actual robots one by one
- Build a phone-friendly dashboard
- Add voice control
- Let robots talk to each other (one finishes a task, hands off to another)

## The fun part

This is a learning project to get hands-on with embedded systems, robotics, AI, and distributed computing all at once. Every commit is me figuring something new out.
