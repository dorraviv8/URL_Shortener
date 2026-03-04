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

    stage('Run Tests') {
      steps {
        container('python') {
          sh '''
            pip install -r app/requirements.txt
            pip install pytest httpx
            pytest -v
          '''
        }
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