pipeline {
    agent any

    environment {
        PYINSTALLER_SPEC = 'app.spec'
        INNOSETUP_EXE = 'C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe'
        PATH = "C:\\ProgramData\\chocolatey\\bin;${env.PATH}"
    }

    stages {
        stage('Setup') {
            steps {
                echo 'Installing dependencies...'
                bat 'python -m pip install -r requirements.txt'
            }
        }

        stage('Build App') {
            steps {
                echo 'Running PyInstaller...'
                bat "pyinstaller %PYINSTALLER_SPEC%"
            }
        }

        stage('Create Installer') {
            steps {
                echo 'Building installer with Inno Setup...'
                bat "\"%INNOSETUP_EXE%\" installer.iss"
            }
        }

        stage('Archive Build') {
            steps {
                archiveArtifacts artifacts: 'dist/**/*.*', allowEmptyArchive: true
            }
        }
    }
}
