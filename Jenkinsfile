pipeline {
    agent any
    environment {
        EC2_HOST = "ec2-13-40-196-213.eu-west-2.compute.amazonaws.com"
        EC2_USER = "ubuntu"
        APP_DIR  = "learning3"  
        IMAGE_NAME = "sundhar04/githubimage:latest"
        CONTAINER_NAME = "my_app_container_${env.BRANCH_NAME.replaceAll('/', '_')}"
    }

    stages {
        stage("Checkout") {
            steps {
                checkout scm
                script {
                    env.PORT_NUMBER = getBranchPort(env.BRANCH_NAME)
                    echo "Branch: ${env.BRANCH_NAME}, Port: ${env.PORT_NUMBER}, Container: ${env.CONTAINER_NAME}"
                }
            }
        }

        stage("Deploy to EC2 with DevSecOps Setup") {
            steps {
                sshagent(['ec2-ssh-key']) {
                    withCredentials([usernamePassword(credentialsId: 'githubcreddddd', usernameVariable: 'GIT_USERNAME', passwordVariable: 'GIT_PASSWORD')]) {
                        sh '''
ssh -o StrictHostKeyChecking=no $EC2_USER@$EC2_HOST << 'EOF'
set -euo pipefail
cd /home/ubuntu

# Docker Installation
if ! command -v docker &> /dev/null; then
    sudo apt-get update -y
    sudo apt-get install -y ca-certificates curl gnupg lsb-release
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    echo \
      "deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
      https://download.docker.com/linux/ubuntu \
      \$(lsb_release -cs) stable" | \
      sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -y
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    sudo usermod -aG docker ubuntu
fi

# Gitleaks Installation
if ! command -v gitleaks &> /dev/null; then
    curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest \
        | grep "browser_download_url.*linux.*amd64" \
        | cut -d '"' -f 4 \
        | wget -qi -
    chmod +x gitleaks* && sudo mv gitleaks* /usr/local/bin/gitleaks
fi

# Trivy Installation
if ! command -v trivy &> /dev/null; then
    sudo apt install -y wget apt-transport-https gnupg lsb-release
    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -
    echo "deb https://aquasecurity.github.io/trivy-repo/deb \$(lsb_release -sc) main" | \
        sudo tee -a /etc/apt/sources.list.d/trivy.list
    sudo apt update
    sudo apt install -y trivy
fi

# Safety Installation
if ! pip show safety &> /dev/null; then
    pip install safety
fi

# Clone or Update Repo
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR"
    git config pull.rebase false
    git fetch origin
    git reset --hard origin/${env.BRANCH_NAME}
    git pull origin ${env.BRANCH_NAME}
    cd ..
else
    git clone -b ${env.BRANCH_NAME} https://$GIT_USERNAME:$GIT_PASSWORD@github.com/sundhar04/learning3.git
    cd "$APP_DIR"
    git config pull.rebase false
    cd ..
fi

# Secret Scan
cd /home/ubuntu

gitleaks detect --source "$APP_DIR" --exit-code 1 --report-path=gitleaks-report.json

# Dependency Scan
if [ -f "$APP_DIR/requirements.txt" ]; then
    pip install -r "$APP_DIR/requirements.txt"
    safety check -r "$APP_DIR/requirements.txt" --full-report --exit-code 1
fi

# Docker Cleanup
sudo docker stop "${env.CONTAINER_NAME}" || true
sudo docker rm "${env.CONTAINER_NAME}" || true
sudo docker rmi "$IMAGE_NAME" || true

# Build Docker Image
cd "$APP_DIR"
sudo docker build -t "$IMAGE_NAME" .

# Image Scan
trivy image --exit-code 1 --severity HIGH,CRITICAL "$IMAGE_NAME"

# Free Port
EXISTING_CONTAINER=$(sudo docker ps -q --filter "publish=${env.PORT_NUMBER}")
if [ ! -z "$EXISTING_CONTAINER" ]; then
    sudo docker stop $EXISTING_CONTAINER
    sudo docker rm $EXISTING_CONTAINER
fi

# Run Container
sudo docker run -d --name "${env.CONTAINER_NAME}" -p ${env.PORT_NUMBER}:5000 "$IMAGE_NAME"

EOF
                        '''
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

def getBranchPort(branchName) {
    switch(branchName) {
        case 'main':
        case 'master':
            return '8080'
        case 'develop':
        case 'second':
            return '8081'
        case 'staging':
        case 'stage':
            return '8082'
        case 'testing':
        case 'test':
            return '8083'
        default:
            def hash = Math.abs(branchName.hashCode()) % 1000
            return (8100 + hash).toString()
    }
}
