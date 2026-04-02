pipeline {
  agent {
    kubernetes {
      defaultContainer 'jnlp'
      yaml """
apiVersion: v1
kind: Pod
spec:
  serviceAccountName: jenkins
  containers:
    - name: python
      image: python:3.11
      command:
        - cat
      tty: true
      workingDir: /home/jenkins/agent
      volumeMounts:
        - name: workspace-volume
          mountPath: /home/jenkins/agent

    - name: kaniko
      image: gcr.io/kaniko-project/executor:v1.23.2-debug
      command:
        - /busybox/cat
      tty: true
      workingDir: /home/jenkins/agent
      volumeMounts:
        - name: docker-config
          mountPath: /kaniko/.docker
        - name: workspace-volume
          mountPath: /home/jenkins/agent

  volumes:
    - name: docker-config
      secret:
        secretName: kaniko-docker-config
    - name: workspace-volume
      emptyDir: {}
"""
    }
  }

  environment {
    IMAGE = "dorraviv/url-shortener-platform"
    TAG = "${env.BUILD_NUMBER}"
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        script {
          def commitMsg = sh(script: 'git log -1 --pretty=%B', returnStdout: true).trim()
          if (commitMsg.contains('[skip ci]')) {
            currentBuild.result = 'NOT_BUILT'
            error('Skipping: manifest-only commit')
          }
        }
      }
    }

    stage('Quality Checks') {
      steps {
        container('python') {
          sh '''
            pip install -r requirements-dev.txt
            flake8 app
            pytest -v
          '''
        }
      }
    }

    stage('Build & Push Image') {
      steps {
        container('kaniko') {
          sh '''
            /kaniko/executor \
              --dockerfile=Dockerfile \
              --context=dir://$PWD \
              --destination=${IMAGE}:${TAG} \
              --destination=${IMAGE}:latest \
              --verbosity=info
          '''
        }
      }
    }

    stage('Update Manifest') {
      steps {
        withCredentials([usernamePassword(credentialsId: 'github-creds', usernameVariable: 'GIT_USER', passwordVariable: 'GIT_TOKEN')]) {
          sh '''
            git config user.email "jenkins@ci"
            git config user.name "Jenkins"
            git checkout -B main
            sed -i "s|image: dorraviv/url-shortener-platform:.*|image: dorraviv/url-shortener-platform:${TAG}|" k8s/app-deployment.yaml
            git add k8s/app-deployment.yaml
            git commit -m "ci: update image to ${TAG} [skip ci]"
            git push https://${GIT_USER}:${GIT_TOKEN}@github.com/dorraviv8/URL_Shortener.git HEAD:main
          '''
        }
      }
    }

  }

  post {
    success {
      echo "Pipeline succeeded: ${IMAGE}:${TAG} — ArgoCD will sync from git"
    }
    failure {
      echo "Pipeline failed on branch ${env.BRANCH_NAME}, build #${env.BUILD_NUMBER}"
    }
  }
}

