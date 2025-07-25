pipeline {
    agent any
    environment {
        EC2_HOST = "ec2-13-40-196-213.eu-west-2.compute.amazonaws.com"
        EC2_USER = "ubuntu"
        APP_DIR  = "learning3"  
        IMAGE_NAME = "sundhar04/githubimage:latest"
        CONTAINER_NAME = "my_app_container_${env.BRANCH_NAME.replaceAll('/', '_')}"
        // Set to 'true' to enable security scans, 'false' to skip them
        ENABLE_SECURITY_SCANS = "true"
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
                            def enableScans = env.ENABLE_SECURITY_SCANS

                            sh """
                            ssh -o StrictHostKeyChecking=no \$EC2_USER@\$EC2_HOST << 'ENDSSH'
                            set -euxo pipefail

                            APP_DIR=${app}
                            BRANCH_NAME=${branch}
                            IMAGE_NAME=${image}
                            CONTAINER_NAME=${container}
                            PORT_NUMBER=${port}
                            ENABLE_SCANS=${enableScans}

                            echo "=== Starting deployment for branch: \$BRANCH_NAME ==="
                            echo "Security scans enabled: \$ENABLE_SCANS"
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

                            # Security Tools Installation (conditional)
                            if [ "\$ENABLE_SCANS" = "true" ]; then
                                echo "=== Installing Security Tools ==="
                                
                                # Install Gitleaks
                                if ! command -v gitleaks &> /dev/null; then
                                    echo "Installing Gitleaks..."
                                    GITLEAKS_VERSION="8.21.2"
                                    GITLEAKS_URL="https://github.com/gitleaks/gitleaks/releases/download/v\${GITLEAKS_VERSION}/gitleaks_\${GITLEAKS_VERSION}_linux_x64.tar.gz"
                                    
                                    wget -O gitleaks.tar.gz "\$GITLEAKS_URL" && \\
                                    tar -xzf gitleaks.tar.gz && \\
                                    chmod +x gitleaks && \\
                                    sudo mv gitleaks /usr/local/bin/gitleaks && \\
                                    rm -f gitleaks.tar.gz LICENSE README.md && \\
                                    echo "Gitleaks installed successfully" || {
                                        echo "WARNING: Failed to install Gitleaks, continuing without secret scanning"
                                        ENABLE_SCANS="partial"
                                    }
                                fi

                                # Install Trivy
                                if ! command -v trivy &> /dev/null; then
                                    echo "Installing Trivy..."
                                    export DEBIAN_FRONTEND=noninteractive
                                    sudo apt update -y && \\
                                    sudo apt install -y wget apt-transport-https gnupg lsb-release && \\
                                    wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add - && \\
                                    echo "deb https://aquasecurity.github.io/trivy-repo/deb \$(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list && \\
                                    sudo apt update -y && \\
                                    sudo apt install -y trivy && \\
                                    echo "Trivy installed successfully" || {
                                        echo "WARNING: Failed to install Trivy, continuing without container scanning"
                                        ENABLE_SCANS="partial"
                                    }
                                fi

                                # Try to set up Safety (with fallbacks)
                                echo "Setting up Safety for dependency scanning..."
                                export DEBIAN_FRONTEND=noninteractive
                                
                                # Method 1: Try pipx (cleanest)
                                if sudo apt install -y pipx python3-venv && pipx install safety; then
                                    echo "Safety installed via pipx"
                                    SAFETY_CMD="pipx run safety"
                                # Method 2: Try system-wide with override
                                elif sudo apt install -y python3-pip && pip3 install --break-system-packages safety; then
                                    echo "Safety installed system-wide"
                                    SAFETY_CMD="python3 -m safety"
                                else
                                    echo "WARNING: Could not install Safety, skipping dependency scanning"
                                    SAFETY_CMD=""
                                    ENABLE_SCANS="partial"
                                fi
                            else
                                echo "Security scans disabled, skipping tool installation"
                                SAFETY_CMD=""
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

                            # Security Scans (conditional)
                            if [ "\$ENABLE_SCANS" = "true" ] || [ "\$ENABLE_SCANS" = "partial" ]; then
                                echo "=== Running Security Scans ==="
                                
                                # Gitleaks Scan
                                if command -v gitleaks &> /dev/null; then
                                    echo "Running Gitleaks scan..."
                                    /usr/local/bin/gitleaks detect --source "\$APP_DIR" --exit-code 1 --report-path=gitleaks-report.json || {
                                        echo "ERROR: Gitleaks detected secrets!"
                                        if [ -f gitleaks-report.json ]; then
                                            echo "Gitleaks Report:"
                                            cat gitleaks-report.json
                                        fi
                                        exit 1
                                    }
                                    echo "Gitleaks scan passed"
                                else
                                    echo "Gitleaks not available, skipping secret scan"
                                fi

                                # Safety Scan
                                if [ -f "\$APP_DIR/requirements.txt" ] && [ ! -z "\$SAFETY_CMD" ]; then
                                    echo "Running dependency vulnerability scan..."
                                    
                                    # Install dependencies first
                                    if pip3 install --break-system-packages -r "\$APP_DIR/requirements.txt" 2>/dev/null || \\
                                       pip3 install --user -r "\$APP_DIR/requirements.txt" 2>/dev/null; then
                                        echo "Dependencies installed"
                                    else
                                        echo "WARNING: Could not install dependencies for scanning"
                                    fi
                                    
                                    # Run safety check
                                    \$SAFETY_CMD check -r "\$APP_DIR/requirements.txt" --full-report --exit-code 1 || {
                                        echo "ERROR: Safety scan found vulnerabilities!"
                                        exit 1
                                    }
                                    echo "Safety scan passed"
                                else
                                    echo "Skipping dependency scan (no requirements.txt or Safety not available)"
                                fi
                            else
                                echo "Security scans disabled"
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

                            # Container Image Vulnerability Scan (conditional)
                            if [ "\$ENABLE_SCANS" = "true" ] || [ "\$ENABLE_SCANS" = "partial" ]; then
                                if command -v trivy &> /dev/null; then
                                    echo "=== Running Trivy Image Scan ==="
                                    trivy image --exit-code 1 --severity HIGH,CRITICAL "\$IMAGE_NAME" || {
                                        echo "ERROR: Trivy found HIGH/CRITICAL vulnerabilities!"
                                        exit 1
                                    }
                                    echo "Trivy scan passed"
                                else
                                    echo "Trivy not available, skipping container image scan"
                                fi
                            fi

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
                            echo "Security scans: \$ENABLE_SCANS"
                            
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
            echo "Access your application at: http://${env.EC2_HOST}:${env.PORT_NUMBER}"
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
