pipeline {
    agent any
    
    environment {
        APP_NAME = 'url-shortener'
        IMAGE_TAG = "${BUILD_NUMBER}"
        NETWORK_NAME = "test-net-${BUILD_NUMBER}"
    }
    
    options {
        timeout(time: 20, unit: 'MINUTES')
        timestamps()
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo 'Checking out code from GitHub...'
                checkout scm
                echo '✅ Code checked out successfully!'
            }
        }
        
        stage('Create Test Network') {
            steps {
                echo 'Creating isolated Docker network for testing...'
                sh 'docker network create ${NETWORK_NAME}'
                echo '✅ Test network created!'
            }
        }
        
        stage('Start Database') {
            steps {
                echo 'Starting PostgreSQL database...'
                sh """
                docker run -d \\
                    --name test-db-${BUILD_NUMBER} \\
                    --network ${NETWORK_NAME} \\
                    -e POSTGRES_DB=shortener \\
                    -e POSTGRES_USER=user \\
                    -e POSTGRES_PASSWORD=password \\
                    postgres:15-alpine
                """
                echo 'Waiting for database to be ready...'
                sh '''
                for i in {1..30}; do
                    if docker exec test-db-${BUILD_NUMBER} pg_isready -U user -d shortener; then
                        echo "✅ Database is ready!"
                        break
                    fi
                    echo "Waiting for database... ($i/30)"
                    sleep 2
                done
                '''
            }
        }
        
        stage('Build Image') {
            steps {
                script {
                    echo "Building Docker image: ${APP_NAME}:${IMAGE_TAG}"
                    
                    // '.' means "build from the workspace root, where Dockerfile is"
                    docker.build("${APP_NAME}:${IMAGE_TAG}", ".")
                }
            }
        }
        
        stage('Test Image') {
            steps {
                script {
                    echo "Running containerized tests..."
                    
                    // Start the image in our test network
                    sh "docker run -d \\
                        --name test-app-${BUILD_NUMBER} \\
                        --network ${NETWORK_NAME} \\
                        -e DATABASE_URL=postgresql://user:password@test-db-${BUILD_NUMBER}:5432/shortener \\
                        ${APP_NAME}:${IMAGE_TAG}"
                    
                    // Wait 10 seconds for the app inside the container to start up
                    sh 'sleep 10'
                    
                    // Ask Jenkins to hit the app and check for a 200 OK response
                    echo 'Testing application health endpoint...'
                    sh 'curl -f http://test-app-${BUILD_NUMBER}:8000/ || exit 1'
                    
                    // Additional endpoint tests
                    echo 'Testing API documentation endpoint...'
                    sh 'curl -f http://test-app-${BUILD_NUMBER}:8000/docs || exit 1'
                    
                    echo 'Testing URL shortening functionality...'
                    sh '''
                    RESPONSE=$(curl -s -X POST http://test-app-${BUILD_NUMBER}:8000/shorten \
                        -H "Content-Type: application/json" \
                        -d '{"url": "https://example.com"}')
                    echo "Shorten response: $RESPONSE"
                    if [[ ! "$RESPONSE" =~ "short_url" ]]; then
                        echo "❌ URL shortening failed"
                        exit 1
                    fi
                    '''
                    
                    // Stop and remove the test containers
                    sh 'docker stop test-app-${BUILD_NUMBER} || true'
                    sh 'docker rm test-app-${BUILD_NUMBER} || true'
                    sh 'docker stop test-db-${BUILD_NUMBER} || true'
                    sh 'docker rm test-db-${BUILD_NUMBER} || true'
                }
            }
        }
        
        stage('Cleanup Network') {
            steps {
                echo 'Cleaning up test network...'
                sh "docker network rm ${NETWORK_NAME} || true"
                echo '✅ Cleanup complete!'
            }
        }
    }
    
    post {
        always {
            echo 'Cleaning up resources...'
            sh '''
            docker stop test-app-${BUILD_NUMBER} test-db-${BUILD_NUMBER} 2>/dev/null || true
            docker rm test-app-${BUILD_NUMBER} test-db-${BUILD_NUMBER} 2>/dev/null || true
            docker network rm ${NETWORK_NAME} 2>/dev/null || true
            '''
        }
        success {
            echo "🎉🎉🎉 PIPELINE SUCCESSFUL! 🎉🎉🎉"
            echo "Built and tested: ${APP_NAME}:${IMAGE_TAG}"
        }
        failure {
            echo '❌ Pipeline failed. Check the logs above.'
            echo 'Dump container logs for debugging:'
            sh '''
            echo "=== Application logs ==="
            docker logs test-app-${BUILD_NUMBER} 2>/dev/null || echo "No app container logs"
            echo "=== Database logs ==="
            docker logs test-db-${BUILD_NUMBER} 2>/dev/null || echo "No db container logs"
            '''
        }
    }
}