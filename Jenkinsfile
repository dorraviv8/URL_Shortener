pipeline {
  agent {
    kubernetes {
      inheritFrom 'kaniko'
      defaultContainer 'jnlp'
    }
  }

  environment {
    IMAGE = "dorraviv/url-shortener-platform"
    TAG   = "${env.BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
      }
    }

    stage('Build & Push (Kaniko)') {
      steps {
        container('kaniko') {
          sh '''
            /kaniko/executor \
              --dockerfile=Dockerfile \
              --context=$PWD \
              --destination=${IMAGE}:${TAG} \
              --destination=${IMAGE}:latest \
              --verbosity=info
          '''
        }
      }
    }
  }
}