# Automatic Upgrade Method for Full-Module Source Code Deployment

This tutorial is for enthusiasts who deploy all modules from source and want to automatically pull the source code, build it, and start the services with a single command, achieving the most efficient system upgrades.

The project's test platform `https://2662r3426b.vicp.fun` has used this method since it opened, with good results.

For a video tutorial, see the one published by Bilibili creator Bile Labs: [A Step-by-Step Tutorial on Auto-Updating the Open-Source XiaoZhi Server xiaozhi-server and Configuring the Latest MCP Access Point](https://www.bilibili.com/video/BV15H37zHE7Q)

# Prerequisites
- Your computer/server runs a Linux operating system.
- You have already completed the entire setup process successfully.
- You like following the latest features but find manual deployment every time a hassle, and want an automatic update method.

The second condition is mandatory, because some files involved in this tutorial, such as the JDK, Node.js environment, and Conda environment, only exist after you have completed the entire setup. If you have not, you may not understand what I mean when I mention a certain file.

# What This Tutorial Achieves
- Solves the problem of being unable to pull the latest project source code in mainland China
- Automatically pulls the code and builds the frontend files
- Automatically pulls the code, builds the Java files, kills port 8002, and restarts port 8002
- Automatically pulls the Python code, kills port 8000, and restarts port 8000

# Step 1 Choose Your Project Directory

For example, I planned my project directory as follows. This is a newly created empty directory; you can use the same one if you want to avoid mistakes.
```
/home/system/xiaozhi
```

# Step 2 Clone This Project
First, run the first command to pull the source code. This command works for servers and computers on networks in mainland China without a VPN.

```
cd /home/system/xiaozhi
git clone https://ghproxy.net/https://github.com/xinnan-tech/xiaozhi-esp32-server.git
```

After it finishes, your project directory will contain a folder named `xiaozhi-esp32-server`, which holds the project source code.

# Step 3 Copy the Base Files

If you have completed the whole setup before, you are familiar with the FunASR model file `xiaozhi-server/models/SenseVoiceSmall/model.pt` and your private configuration file `xiaozhi-server/data/.config.yaml`.

Now copy the `model.pt` file to the new directory. You can do it like this:
```
# Create the required directories
mkdir -p /home/system/xiaozhi/xiaozhi-esp32-server/main/xiaozhi-server/data/

cp full-path-to-your-existing-.config.yaml /home/system/xiaozhi/xiaozhi-esp32-server/main/xiaozhi-server/data/.config.yaml
cp full-path-to-your-existing-model.pt /home/system/xiaozhi/xiaozhi-esp32-server/main/xiaozhi-server/models/SenseVoiceSmall/model.pt
```

# Step 4 Create Three Automatic Build Scripts

## 4.1 Automatically Build the manager-web Module
In `/home/system/xiaozhi/`, create a file named `update_8001.sh` with the following content:

```
cd /home/system/xiaozhi/xiaozhi-esp32-server
git fetch --all
git reset --hard
git pull origin main


cd /home/system/xiaozhi/xiaozhi-esp32-server/main/manager-web
npm install
npm run build
rm -rf /home/system/xiaozhi/manager-web
mv /home/system/xiaozhi/xiaozhi-esp32-server/main/manager-web/dist /home/system/xiaozhi/manager-web
```

After saving, run the permission command:
```
chmod 777 update_8001.sh
```
Then continue below.

## 4.2 Automatically Build and Run the manager-api Module
In `/home/system/xiaozhi/`, create a file named `update_8002.sh` with the following content:

```
cd /home/system/xiaozhi/xiaozhi-esp32-server
git pull origin main


cd /home/system/xiaozhi/xiaozhi-esp32-server/main/manager-api
rm -rf target
mvn clean package -Dmaven.test.skip=true
cd /home/system/xiaozhi/

# Find the PID of the process using port 8002
PID=$(sudo netstat -tulnp | grep 8002 | awk '{print $7}' | cut -d'/' -f1)

rm -rf /home/system/xiaozhi/xiaozhi-esp32-api.jar
mv /home/system/xiaozhi/xiaozhi-esp32-server/main/manager-api/target/xiaozhi-esp32-api.jar /home/system/xiaozhi/xiaozhi-esp32-api.jar

# Check whether a PID was found
if [ -z "$PID" ]; then
  echo "No process using port 8002 found"
else
  echo "Found process using port 8002, PID: $PID"
  # Kill the process
  kill -9 $PID
  kill -9 $PID
  echo "Killed process $PID"
fi

nohup java -jar xiaozhi-esp32-api.jar --spring.profiles.active=dev &

tail -f nohup.out
```

After saving, run the permission command:
```
chmod 777 update_8002.sh
```
Then continue below.

## 4.3 Automatically Build and Run the Python Project
In `/home/system/xiaozhi/`, create a file named `update_8000.sh` with the following content:

```
cd /home/system/xiaozhi/xiaozhi-esp32-server
git pull origin main

# Find the PID of the process using port 8000
PID=$(sudo netstat -tulnp | grep 8000 | awk '{print $7}' | cut -d'/' -f1)

# Check whether a PID was found
if [ -z "$PID" ]; then
  echo "No process using port 8000 found"
else
  echo "Found process using port 8000, PID: $PID"
  # Kill the process
  kill -9 $PID
  kill -9 $PID
  echo "Killed process $PID"
fi
cd main/xiaozhi-server
# Initialize the conda environment
source ~/.bashrc
conda activate xiaozhi-esp32-server
pip install -r requirements.txt
nohup python app.py >/dev/null &
tail -f /home/system/xiaozhi/xiaozhi-esp32-server/main/xiaozhi-server/tmp/server.log
```

After saving, run the permission command:
```
chmod 777 update_8000.sh
```
Then continue below.

# Daily Updates

Once the scripts above are in place, for daily updates simply run the following commands in order to update and restart automatically:

```
cd /home/system/xiaozhi
# Update and start the web program
./update_8001.sh
# Update and start the Java program
./update_8002.sh
# Update and start the Python program
./update_8000.sh


# To view the Java logs later, run:
tail -f nohup.out
# To view the Python logs later, run:
tail -f /home/system/xiaozhi/xiaozhi-esp32-server/main/xiaozhi-server/tmp/server.log
```

# Notes
The test platform `https://2662r3426b.vicp.fun` uses Nginx as a reverse proxy. The detailed nginx.conf configuration can be [found here](https://github.com/xinnan-tech/xiaozhi-esp32-server/issues/791).

## FAQ

### 1. Why don't I see port 8001?
Answer: 8001 is used in development to serve the frontend. For a server deployment, it is not recommended to run the frontend on port 8001 with `npm run serve`; instead, build it into HTML files as shown in this tutorial and use Nginx to manage access.

### 2. Do I need to run SQL statements manually for every update?
Answer: No. The project uses **Liquibase** to manage database versions, and new SQL scripts are executed automatically.
