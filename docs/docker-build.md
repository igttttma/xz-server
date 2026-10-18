# How to Build Docker Images Locally

This project now uses GitHub's `automatic Docker image builds`. If you pull the images released by the project and have no need to build your own, ignore this document.

If you have modified the source code and want to deploy it with `Docker`, follow the steps below:

## 1. Environment Preparation

Install Docker:
```bash
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

## 2. Build the Images

After modifying the code, follow these steps to build new images:

Prepare `your username` and `a new version number`.
- `your username` is your username registered on `Docker Hub`, for example `xiaozhi`. If you do not need to push to `Docker Hub`, you can define it freely.
- `a new version number` is the version of the image you build, for example `1.2.3`. You can customize it or use a date format (such as `20260609`) to distinguish it from the currently running version and to remember when you built it. It must differ from the version currently running on your machine.

Enter the `xiaozhi-esp32-server` project root and build the server and web images:

```bash
cd project-root

# Build the server image
docker build -f Dockerfile-server -t your-username/xiaozhi-esp32-server:new-version .

# Build the web image
docker build -f Dockerfile-web -t your-username/xiaozhi-esp32-server-web:new-version .

```

## 3. Modify the docker-compose Configuration

```bash
cd main/xiaozhi-server
```

Edit the `docker-compose_all.yml` file and replace the image versions with the ones you just built:

```yaml
services:
  xiaozhi-esp32-server:
    image: your-username/xiaozhi-esp32-server:new-version   # Change to your image address
    ...

  xiaozhi-esp32-server-web:
    image: your-username/xiaozhi-esp32-server-web:new-version   # Change to your image address
    ...
```

## 4. Restart the Services

```bash
# Stop the old containers
docker compose -f docker-compose_all.yml down

# Start the new containers
docker compose -f docker-compose_all.yml up -d
```

## 5. Verify

Check the logs to confirm the services started normally:

```bash
# View the server logs
docker logs -f -n 50 xiaozhi-esp32-server

# View the web logs
docker logs -f -n 50 xiaozhi-esp32-server-web
```
