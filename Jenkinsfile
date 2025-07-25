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

                            sh """
                            ssh -o StrictHostKeyChecking=no \$EC2_USER@\$EC2_HOST << 'EOF'
                            set -euxo pipefail

                            APP_DIR=${app}
                            BRANCH_NAME=${branch}
                            IMAGE_NAME=${image}
                            CONTAINER_NAME=${container}
                            PORT_NUMBER=${port}

                            cd /home/ubuntu

                            # Check if Docker is installed and user is in docker group
                            if ! command -v docker &> /dev/null; then
                                echo "Docker not found. Please install Docker and add ubuntu user to docker group manually."
                                exit 1
                            fi

                            # Test docker access without sudo
                            if ! docker ps &> /dev/null; then
                                echo "Docker requires sudo. Please add ubuntu user to docker group and restart session."
                                echo "Run: sudo usermod -aG docker ubuntu && newgrp docker"
                                exit 1
                            fi

                            # Gitleaks Installation (only if not present)
                            if ! command -v gitleaks &> /dev/null; then
                                curl -s https://api.github.com/repos/gitleaks/gitleaks/releases/latest |
                                grep "browser_download_url.*linux.*amd64" |
                                cut -d '"' -f 4 |
                                wget -qi -
                                chmod +x gitleaks* && sudo mv gitleaks* /usr/local/bin/gitleaks || {
                                    echo "Failed to install gitleaks. Please install manually."
                                    exit 1
                                }
                            fi

                            # Trivy Installation (only if not present)
                            if ! command -v trivy &> /dev/null; then
                                echo "Trivy not found. Please install Trivy manually."
                                echo "Installation commands:"
                                echo "sudo apt install -y wget apt-transport-https gnupg lsb-release"
                                echo "wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | sudo apt-key add -"
                                echo "echo 'deb https://aquasecurity.github.io/trivy-repo/deb \$(lsb_release -sc) main' | sudo tee -a /etc/apt/sources.list.d/trivy.list"
                                echo "sudo apt update && sudo apt install -y trivy"
                                exit 1
                            fi

                            # Safety Installation
                            if ! pip show safety &> /dev/null; then
                                pip install --user safety || {
                                    echo "Failed to install safety. Please install manually."
                                    exit 1
                                }
                            fi

                            # Clone or Update Repo
                            if [ -d "\$APP_DIR" ]; then
                                cd "\$APP_DIR"
                                git config pull.rebase false
                                git fetch origin
                                git reset --hard origin/\$BRANCH_NAME
                                git pull origin \$BRANCH_NAME
                                cd ..
                            else
                                git clone -b \$BRANCH_NAME https://${GIT_USERNAME}:${GIT_PASSWORD}@github.com/sundhar04/learning3.git
                            fi

                            # Secret Scan
                            gitleaks detect --source "\$APP_DIR" --exit-code 1 --report-path=gitleaks-report.json || { 
                                echo "Gitleaks detected secrets in the code"
                                cat gitleaks-report.json 2>/dev/null || true
                                exit 1
                            }

                            # Dependency Scan
                            if [ -f "\$APP_DIR/requirements.txt" ]; then
                                pip install --user -r "\$APP_DIR/requirements.txt" || {
                                    echo "Failed to install requirements"
                                    exit 1
                                }
                                ~/.local/bin/safety check -r "\$APP_DIR/requirements.txt" --full-report --exit-code 1 || { 
                                    echo "Safety scan detected vulnerabilities"
                                    exit 1
                                }
                            fi

                            # Docker Cleanup (without sudo)
                            docker stop "\$CONTAINER_NAME" 2>/dev/null || true
                            docker rm "\$CONTAINER_NAME" 2>/dev/null || true
                            docker rmi "\$IMAGE_NAME" 2>/dev/null || true

                            # Build Docker Image
                            cd "\$APP_DIR"
                            docker build -t "\$IMAGE_NAME" . || {
                                echo "Docker build failed"
                                exit 1
                            }

                            # Image Scan
                            trivy image --exit-code 1 --severity HIGH,CRITICAL "\$IMAGE_NAME" || { 
                                echo "Trivy scan found HIGH/CRITICAL vulnerabilities"
                                exit 1
                            }

                            # Free Port
                            EXISTING_CONTAINER=\$(docker ps -q --filter "publish=\$PORT_NUMBER" 2>/dev/null || true)
                            if [ ! -z "\$EXISTING_CONTAINER" ]; then
                                docker stop \$EXISTING_CONTAINER
                                docker rm \$EXISTING_CONTAINER
                            fi

                            # Run Container
                            docker run -d --name "\$CONTAINER_NAME" -p \$PORT_NUMBER:5000 "\$IMAGE_NAME" || {
                                echo "Failed to start container"
                                exit 1
                            }

                            echo "Container \$CONTAINER_NAME started successfully on port \$PORT_NUMBER"
                            docker ps | grep "\$CONTAINER_NAME"

EOF
                            """
                        }
                    }
                }
            }
        }
    }

    post {
        success {
            echo "Deployment successful"
        }
        failure {
            echo "Deployment failed"
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
