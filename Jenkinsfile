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
                        script {
                            def branch = env.BRANCH_NAME
                            def image = env.IMAGE_NAME
                            def container = env.CONTAINER_NAME
                            def port = env.PORT_NUMBER
                            def app = env.APP_DIR
                            def gitUsername = env.GIT_USERNAME
                            def gitPassword = env.GIT_PASSWORD

                            sh """
                            ssh -o StrictHostKeyChecking=no \$EC2_USER@\$EC2_HOST << 'ENDSSH'
                            set -euxo pipefail

                            APP_DIR=${app}
                            BRANCH_NAME=${branch}
                            IMAGE_NAME=${image}
                            CONTAINER_NAME=${container}
                            PORT_NUMBER=${port}

                            echo "=== Starting deployment for branch: \$BRANCH_NAME ==="
                            cd /home/ubuntu

                            # Check Docker installation and access
                            echo "=== Checking Docker ==="
                            if ! command -v docker &> /dev/null; then
                                echo "ERROR: Docker not found!"
                                exit 1
                            fi

                            if ! docker ps &> /dev/null; then
                                echo "ERROR: Cannot access Docker without sudo!"
                                exit 1
                            fi
                            echo "Docker is accessible"

                            # Install Gitleaks with better error handling
                            echo "=== Installing/Checking Gitleaks ==="
                            if ! command -v gitleaks &> /dev/null; then
                                echo "Installing Gitleaks..."
                                GITLEAKS_VERSION="8.21.2"
                                GITLEAKS_URL="https://github.com/gitleaks/gitleaks/releases/download/v\${GITLEAKS_VERSION}/gitleaks_\${GITLEAKS_VERSION}_linux_x64.tar.gz"
                                
                                wget -O gitleaks.tar.gz "\$GITLEAKS_URL" || {
                                    echo "Failed to download Gitleaks from GitHub releases"
                                    exit 1
                                }
                                
                                tar -xzf gitleaks.tar.gz || {
                                    echo "Failed to extract Gitleaks"
                                    exit 1
                                }
                                
                                chmod +x gitleaks
                                sudo mv gitleaks /usr/local/bin/gitleaks || {
                                    echo "Failed to move Gitleaks to /usr/local/bin"
                                    exit 1
                                }
                                
                                rm -f gitleaks.tar.gz LICENSE README.md
                                echo "Gitleaks installed successfully"
                            else
                                echo "Gitleaks already installed"
                            fi

                            # Install Trivy with better error handling
                            echo "=== Installing/Checking Trivy ==="
                            if ! command -v trivy &> /dev/null; then
                                echo "Installing Trivy..."
                                sudo apt update -y
                                sudo apt install -y wget apt-transport-https gnupg lsb-release
                                
                                wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add - || {
                                    echo "Failed to add Trivy GPG key"
                                    exit 1
                                }
                                
                                echo "deb https://aquasecurity.github.io/trivy-repo/deb \$(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
                                sudo apt update -y
                                sudo apt install -y trivy || {
                                    echo "Failed to install Trivy"
                                    exit 1
                                }
                                echo "Trivy installed successfully"
                            else
                                echo "Trivy already installed"
                            fi

                            # Install Safety
                            echo "=== Installing/Checking Safety ==="
                            if ! pip3 show safety &> /dev/null; then
                                echo "Installing Safety..."
                                pip3 install --user safety || {
                                    echo "Failed to install Safety"
                                    exit 1
                                }
                                echo "Safety installed successfully"
                            else
                                echo "Safety already installed"
                            fi

                            # Clone or Update Repository
                            echo "=== Cloning/Updating Repository ==="
                            if [ -d "\$APP_DIR" ]; then
                                echo "Updating existing repository"
                                cd "\$APP_DIR"
                                git config pull.rebase false
                                git fetch origin
                                git reset --hard origin/\$BRANCH_NAME
                                git pull origin \$BRANCH_NAME || {
                                    echo "Failed to pull latest changes"
                                    exit 1
                                }
                                cd ..
                            else
                                echo "Cloning repository"
                                git clone -b \$BRANCH_NAME https://${gitUsername}:${gitPassword}@github.com/sundhar04/learning3.git || {
                                    echo "Failed to clone repository"
                                    exit 1
                                }
                            fi

                            # Security Scans
                            echo "=== Running Gitleaks Scan ==="
                            /usr/local/bin/gitleaks detect --source "\$APP_DIR" --exit-code 1 --report-path=gitleaks-report.json || {
                                echo "ERROR: Gitleaks detected secrets!"
                                if [ -f gitleaks-report.json ]; then
                                    echo "Gitleaks Report:"
                                    cat gitleaks-report.json
                                fi
                                exit 1
                            }
                            echo "Gitleaks scan passed"

                            # Dependency Vulnerability Scan
                            echo "=== Running Safety Scan ==="
                            if [ -f "\$APP_DIR/requirements.txt" ]; then
                                echo "Installing Python dependencies..."
                                pip3 install --user -r "\$APP_DIR/requirements.txt" || {
                                    echo "Failed to install Python dependencies"
                                    exit 1
                                }
                                
                                echo "Running Safety scan..."
                                ~/.local/bin/safety check -r "\$APP_DIR/requirements.txt" --full-report --exit-code 1 || {
                                    echo "ERROR: Safety scan found vulnerabilities!"
                                    exit 1
                                }
                                echo "Safety scan passed"
                            else
                                echo "No requirements.txt found, skipping dependency scan"
                            fi

                            # Docker Operations
                            echo "=== Docker Operations ==="
                            echo "Stopping and removing existing container..."
                            docker stop "\$CONTAINER_NAME" 2>/dev/null || echo "Container not running"
                            docker rm "\$CONTAINER_NAME" 2>/dev/null || echo "Container not found"
                            docker rmi "\$IMAGE_NAME" 2>/dev/null || echo "Image not found"

                            echo "Building Docker image..."
                            cd "\$APP_DIR"
                            docker build -t "\$IMAGE_NAME" . || {
                                echo "ERROR: Docker build failed!"
                                exit 1
                            }
                            echo "Docker build successful"

                            # Container Image Vulnerability Scan
                            echo "=== Running Trivy Image Scan ==="
                            trivy image --exit-code 1 --severity HIGH,CRITICAL "\$IMAGE_NAME" || {
                                echo "ERROR: Trivy found HIGH/CRITICAL vulnerabilities!"
                                exit 1
                            }
                            echo "Trivy scan passed"

                            # Port Management
                            echo "=== Managing Ports ==="
                            EXISTING_CONTAINER=\$(docker ps -q --filter "publish=\$PORT_NUMBER" 2>/dev/null || true)
                            if [ ! -z "\$EXISTING_CONTAINER" ]; then
                                echo "Stopping container using port \$PORT_NUMBER"
                                docker stop \$EXISTING_CONTAINER
                                docker rm \$EXISTING_CONTAINER
                            fi

                            # Deploy Container
                            echo "=== Deploying Container ==="
                            docker run -d --name "\$CONTAINER_NAME" -p \$PORT_NUMBER:5000 "\$IMAGE_NAME" || {
                                echo "ERROR: Failed to start container!"
                                exit 1
                            }

                            echo "=== Deployment Successful ==="
                            echo "Container: \$CONTAINER_NAME"
                            echo "Port: \$PORT_NUMBER"
                            echo "Image: \$IMAGE_NAME"
                            
                            # Verify deployment
                            sleep 5
                            if docker ps | grep -q "\$CONTAINER_NAME"; then
                                echo "Container is running successfully"
                                docker ps | grep "\$CONTAINER_NAME"
                            else
                                echo "ERROR: Container failed to start!"
                                docker logs "\$CONTAINER_NAME" 2>/dev/null || true
                                exit 1
                            fi

ENDSSH
                            """
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "=== DEPLOYMENT SUCCESSFUL ==="
            echo "Application deployed on port ${env.PORT_NUMBER}"
            echo "Container: ${env.CONTAINER_NAME}"
        }
        failure {
            echo "=== DEPLOYMENT FAILED ==="
            echo "Check the logs above for error details"
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
