define(["require", "base/js/namespace", "base/js/dialog", "./util"], function (require) {
    "use strict";

    const Jupyter = require('base/js/namespace');
    const dialog = require('base/js/dialog');
    const { jsonRequest } = require("./util");

    const formPromise = fetch('/fair-cells/templates/form.html').then(resp => resp.text());

    const formElements = {};
    const buttonElements = {};
    let elms;

    let notebook;
    let currTab = 'build';

    const getElements = () => {
        return {
            imageNameInput: document.getElementById('image-name'),
            baseImageSelector: document.getElementById('base-image'),
            cellSelector: document.getElementById('cell-index'),
            environmentArea: document.getElementById('environment-area'),

            runPortInput: document.getElementById('run-port'),

            buildButton: document.getElementById('build-container-button'),
            buildOutput: document.getElementById('build-output'),
            buildNotify: document.getElementById('build-notify'),

            buildDockerfileButton: document.getElementById('build-dockerfile-button'),
            buildDockerFileOutput: document.getElementById('build-dockerfile-output'),
            buildDockerFileNotify: document.getElementById('build-dockerfile-notify'),

            runButton: document.getElementById('run-button'),
            statusButton: document.getElementById('status-button'),
            stopButton: document.getElementById('stop-button'),

            cellPreview: document.getElementById('cell-preview'),
            containerStatus: document.getElementById('container-status'),


            loginButton: document.getElementById('docker-registry-login-button'),
            dockerRepositoryInput: document.getElementById('docker-registry'),
            dockerUsernameInput: document.getElementById('docker-registry-username'),
            dockerTokenInput: document.getElementById('docker-registry-token'),
            imageTable: document.getElementById('image-table'),
//            imageTable2: document.getElementById('image-table2'),
            loader: document.getElementById('loader'),
            publishButton: document.getElementById('publish-images-button'),
            kernelSpecific: document.getElementById('kernel-specific')
        }
    }

    const switchTab = async (newTab) => {
        Object.keys(formElements).forEach(k => {
            formElements[k].classList.add('hide');
        });

        formElements[newTab].classList.remove('hide');

        currTab = newTab;
    };


    const setCellSelectOptions = () => {
        // Allow the user to only select code cells.
        Jupyter.notebook.get_cells()
            .map((cell, idx) => cell.cell_type == 'code' ? idx : null)
            .filter(idx => idx !== null)
            .forEach(idx => {
                const opt = document.createElement('option');
                opt.value = idx;
                opt.innerHTML = `Cell ${idx}`

                elms.cellSelector.appendChild(opt);
            })

        elms.cellSelector.onchange = async (e) => {
            const idx = Number(elms.cellSelector.value)
            const cellPreviewElm = Jupyter.notebook.get_cell(idx).output_area.wrapper[0];
            const outputElm = cellPreviewElm.getElementsByClassName('output_subarea')[0];

            if (outputElm) {
                elms.cellPreview.innerHTML = outputElm.innerHTML;
            } else {
                elms.cellPreview.innerHTML = '<p>Output not rendered.</p>';
            }

            const inspectorResp = await fetch(`/fair-cells/notebook/${notebook.path}/inspect/inspector.html?cellIdx=${idx}`);
            if (inspectorResp.status === 501) {
                // No inspector for this Kernel
                return;
            } else if (!inspectorResp.ok) {
                return alert(await inspectorResp.text());
            }

            elms.kernelSpecific.innerHTML = await inspectorResp.text();

        }

        elms.cellSelector.onchange(null);
    }

    const handleBuildDockerFileButtonClick = async (e) => {
        e.preventDefault();

        elms.buildDockerfileButton.value = 'Building Dockerfile...';
        elms.buildDockerfileButton.disabled = true;
        elms.buildDockerFileOutput.value = '';

        const variables = {};
        document.querySelectorAll(`input[data-variable]:checked`).forEach(elm => {
            variables[elm.dataset.variable] = elm.value
        })

        let timeoutId = setTimeout(() => {
            elms.buildNotify.innerHTML = "This might take a while..."

            timeoutId = setTimeout(() => {
                elms.buildNotify.innerHTML = "Especially the first time ..."
            }, 5000)
        }, 5000)

        const res = await jsonRequest('POST', `/fair-cells/notebook/${notebook.path}/build_docker_file`, {
            imageName: elms.imageNameInput.value,
            baseImage: elms.baseImageSelector.value,
            cellIndex: elms.cellSelector.value,
            environment: elms.environmentArea.value,
            variables: variables
        })

        clearTimeout(timeoutId);
        elms.buildNotify.innerHTML = ""

        if (res.status !== 200) {
            return alert(await res.text())
        }

        const data = await res.json()

        elms.buildDockerfileButton.value = 'Build Dockerfile';
        elms.buildDockerfileButton.disabled = false;
        elms.buildDockerFileOutput.value = data['dockerFile']
    }

    const handleLoginButtonClick = async (e) => {
        e.preventDefault();
        elms.loginButton.disabled = true;

        const res = await jsonRequest('POST', `/fair-cells/notebook/${notebook.path}/login`, {
            dockerRepository: elms.dockerRepositoryInput.value,
            dockerUsername: elms.dockerUsernameInput.value,
            dockerToken: elms.dockerTokenInput.value
        })
//
//        clearTimeout(timeoutId);
//        elms.buildNotify.innerHTML = ""
        elms.loginButton.disabled = false;
        if (res.status !== 200) {
//                return alert(await res.text())
            return alert(await 'Unauthorized '+elms.dockerRepositoryInput.value+': unauthorized: incorrect username or password')
        }
//
//        const data = await res.json()


        return alert(await 'Login Successful')
    }


    const handlePublishClick = async (e) => {
        e.preventDefault();
        elms.loader.classList.remove('hide')
        elms.publishButton.disabled = true;
        elms.loginButton.disabled = true;


        let imageNames = []

        imageNames.push(elms.imageNameInput.value);
        console.log('imageNames: '+imageNames)
        const res = await jsonRequest('POST', `/fair-cells/notebook/${notebook.path}/publish`, {
            images: imageNames
        })

        elms.loginButton.disabled = false;
        if (res.status !== 200) {
            return alert(await res.text())
        }
        elms.publishButton.disabled = false;
        elms.loader.classList.add('hide')
        return alert(await 'Publish Successful')
    }


    const handlebuildContainerButtonClick = async (e) => {
        e.preventDefault();
        elms.loader.classList.remove('hide')
        elms.buildButton.value = 'Building Container...';
        elms.buildButton.disabled = true;
        elms.buildOutput.value = '';

        const variables = {};
        document.querySelectorAll(`input[data-variable]:checked`).forEach(elm => {
            variables[elm.dataset.variable] = elm.value
        })

        let timeoutId = setTimeout(() => {
            elms.buildNotify.innerHTML = "This might take a while..."

            timeoutId = setTimeout(() => {
                elms.buildNotify.innerHTML = "Especially the first time ..."
            }, 5000)
        }, 5000)

        const res = await jsonRequest('POST', `/fair-cells/notebook/${notebook.path}/build`, {
            imageName: elms.imageNameInput.value,
            baseImage: elms.baseImageSelector.value,
            cellIndex: elms.cellSelector.value,
            environment: elms.environmentArea.value,
            variables: variables
        })

        clearTimeout(timeoutId);
        elms.buildNotify.innerHTML = ""

        if (res.status !== 200) {
            return alert(await res.text())
        }
        elms.loader.classList.add('hide')
        const data = await res.json()

        elms.buildButton.value = 'Build';
        elms.buildButton.disabled = false;
        elms.buildOutput.value = data['logs']

    }

    const handleRunButtonClick = async (e) => {
        e.preventDefault();
        let selectedImageName = ''

        elms.runButton.value = 'Running...';
        elms.runButton.disabled = true;

        const imageName = elms.imageNameInput.value;
        const res = await jsonRequest('POST', `/fair-cells/image/${imageName}/command/run`, {
            port: Number(elms.runPortInput.value)
        })

        if (res.status !== 200) {
            return alert(await res.text())
        }

        const data = await res.json()

        elms.runButton.value = 'Run';
        elms.runButton.disabled = false;

        elms.containerStatus.value = data['data'];
    };

    const handleStatusButtonClick = async (e) => {
        e.preventDefault();

        const imageName = elms.imageNameInput.value;
        const res = await jsonRequest('GET', `/fair-cells/image/${imageName}/command/status`)

        if (res.status !== 200) {
            return alert(await res.text())
        }

        const data = await res.json()
        
        elms.containerStatus.value = data['data'];
    }

    const handleStopButtonClick = async (e) => {
        e.preventDefault();

        const imageName = elms.imageNameInput.value;
        const res = await jsonRequest('POST', `/fair-cells/image/${imageName}/command/stop`)

        if (res.status !== 200) {
            return alert(await res.text())
        }

        const data = await res.json()

        elms.containerStatus.value = data['data'];
    }


    const onOpen = async () => {
        notebook = await Jupyter.notebook.save_notebook();
        
        buttonElements['build'] = document.getElementById("btn-tab-build");
        buttonElements['run'] = document.getElementById("btn-tab-run");
        buttonElements['publish'] = document.getElementById("btn-tab-publish");
        buttonElements['about'] = document.getElementById("btn-tab-about");

        formElements['build'] = document.getElementById("fair-cells-build");
        formElements['run'] = document.getElementById("fair-cells-run");
        formElements['publish'] = document.getElementById("fair-cells-publish");
        formElements['about'] = document.getElementById("fair-cells-about");

        Object.keys(buttonElements).forEach(k => {
            buttonElements[k].onclick = () => switchTab(k);
        })

        switchTab(currTab);

        elms = getElements();

        setCellSelectOptions(elms.cellSelector, elms.cellPreview);


        elms.buildButton.onclick = handlebuildContainerButtonClick;
        elms.publishButton.onclick = handlePublishClick;
        elms.loginButton.onclick = handleLoginButtonClick;
        elms.buildDockerfileButton.onclick = handleBuildDockerFileButtonClick;
        elms.runButton.onclick = handleRunButtonClick;
        elms.statusButton.onclick = handleStatusButtonClick;
        elms.stopButton.onclick = handleStopButtonClick;

        const res = await jsonRequest('GET', `/fair-cells/notebook/${notebook.path}/environment`)

        if (!res.ok) {
            return alert(await res.text());
        }

        elms.environmentArea.value = (await res.json()).data
    }
    
    return {
        openFormHandler: async () => {
            const formHtml = await formPromise;
    
            dialog.modal({title: 'FAIR-Cells',
                keyboard_manager: Jupyter.keyboard_manager, 
                body: () => formHtml, 
                open: onOpen
            });
        }
    }
});