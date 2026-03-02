pipeline {
    agent {
        kubernetes {
            label 'kaniko'
            defaultContainer 'kaniko'
        }
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build & Push Image') {
            steps {
                sh '''
                /kaniko/executor \
                  --dockerfile=Dockerfile \
                  --context=$(pwd) \
                  --destination=dorraviv/url-shortener-platform:latest \
                  --verbosity=info
                '''
            }
        }
    }
}