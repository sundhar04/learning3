pipeline {
    agent any
    environment {
        EC2_HOST = "ec2-18-175-181-246.eu-west-2.compute.amazonaws.com"
        EC2_USER = "ubuntu"
        APP_DIR  = "learning3"  
        IMAGE_NAME = "sundhar04/githubimage:latest"
        CONTAINER_NAME = "my_app_container_${env.BRANCH_NAME.replaceAll('/', '_')}"
        // PORT_NUMBER will be set dynamically in the script block
    }
    stages {
        stage("Checkout") {
            steps {
               // Use default SCM checkout instead of explicit scmGit to avoid conflicts
               checkout scm
               script {
                   // Set PORT_NUMBER dynamically
                   env.PORT_NUMBER = getBranchPort(env.BRANCH_NAME)
                   echo "Branch: ${env.BRANCH_NAME}, Port: ${env.PORT_NUMBER}, Container: ${env.CONTAINER_NAME}"
               }
            }
        }
        stage("Deploy to EC2") {
            steps {
                sshagent(['ec2-ssh-key']) {
                    withCredentials([usernamePassword(credentialsId: 'githubcreddddd', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                        sh """
ssh -o StrictHostKeyChecking=no \$EC2_USER@\$EC2_HOST << "EOF"
set -e
cd /home/ubuntu
echo "Checking for Docker"
if ! command -v docker &> /dev/null; then
    echo "[!] Docker not found. Installing Docker..."
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \\
      "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \\
      https://download.docker.com/linux/ubuntu \\
      \$(lsb_release -cs) stable" | \\
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker ubuntu
    echo "Docker installed successfully"
else
    echo "Docker is already installed"
fi
echo "Cloning or updating repo"
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull origin ${env.BRANCH_NAME} && cd ..
else
    git clone -b ${env.BRANCH_NAME} https://\$GIT_USERNAME:\$GIT_PASSWORD@github.com/sundhar04/learning3.git
fi
echo "Cleaning old containers and images for branch ${env.BRANCH_NAME}"
sudo docker stop "${env.CONTAINER_NAME}" || true
sudo docker rm "${env.CONTAINER_NAME}" || true
sudo docker rmi "$IMAGE_NAME" || true
echo "Building Docker image"
cd "$APP_DIR"
sudo docker build -t "$IMAGE_NAME" .
echo "Freeing port ${env.PORT_NUMBER} from any running container"
EXISTING_CONTAINER=\$(sudo docker ps -q --filter "publish=${env.PORT_NUMBER}")
if [ ! -z "\$EXISTING_CONTAINER" ]; then
    echo "Found container using port ${env.PORT_NUMBER}: \$EXISTING_CONTAINER"
    sudo docker stop \$EXISTING_CONTAINER
    sudo docker rm \$EXISTING_CONTAINER
fi
echo "Running Docker container"
sudo docker run -d --name "${env.CONTAINER_NAME}" -p ${env.PORT_NUMBER}:5000 "$IMAGE_NAME"
echo "Deployment complete. App running on port ${env.PORT_NUMBER}"
EOF
                        """
                    }
                }
            }
        }
    }
    post {
        success {
            echo "deployment successful"
        }
        failure {
            echo "deployment failed"
        }
    }
}

// Function to determine port based on branch name
def getBranchPort(branchName) {
    switch(branchName) {
        case 'main':
            return '8080'
        case 'master':
            return '8080'
        case 'develop':
            return '8081'
        case 'second':
            return '8081'
        case 'staging':
            return '8082'
        case 'stage':
            return '8082'
        case 'testing':
            return '8083'
        case 'test':
            return '8083'
        default:
            // For feature branches, use a hash-based port to avoid conflicts
            def hash = Math.abs(branchName.hashCode()) % 1000
            return (8100 + hash).toString()
    }
}
