pipeline {
    agent {
        label 'windows'  // Make sure this matches your Windows agent label
    }

    environment {
        PYTHON = 'C:\\Python312\\python.exe'
        INNO_SETUP_PATH = 'C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe'
    }

    stages {
        stage('Checkout') {
            steps {
                git credentialsId: 'github', url: 'https://github.com/selvakumarvmg/appbuilder.git'
            }
        }

        stage('Install Dependencies') {
            steps {
                bat "${env.PYTHON} -m pip install -r requirements.txt"
            }
        }

        stage('Build with PyInstaller') {
            steps {
                bat "${env.PYTHON} -m PyInstaller app.spec"
            }
        }

        stage('Build Installer with Inno Setup') {
            steps {
                bat "\"${env.INNO_SETUP_PATH}\" installer.iss"
            }
        }
    }

    post {
        success {
            echo "Build completed successfully!"
        }
        failure {
            echo "Build failed!"
        }
    }
}
