const fileInput = document.getElementById('file');
const uploadButton = document.getElementById('upload-button');

uploadButton.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a file.');
        return;
    }
    if (!validateFile(file)) {
        alert('Invalid file type or size.');
        return;
    }
    const sasUrl = await fetchSASUrl();
    if (!sasToken) {
        alert('Failed to retrieve SAS token.');
        return;
    }
    await uploadFile(file, sasUrl);
    alert('File uploaded successfully.');
});

function validateFile(file) {
    const allowedTypes = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/vnd.ms-excel'];
    if (!allowedTypes.includes(file.type)) {
        return false;
    }
    if (file.size > 4 * 1024 * 1024) {
        return false;
    }
    return true;
}

async function fetchSASUrl() {
    const response = await fetch('/api/get_sas_url/');
    if (!response.ok) {
        return null;
    }
    const data = await response.json();
    return data.sasUrl;
}

async function uploadFile(file, sasUrl) {
    const xhr = new XMLHttpRequest();
    xhr.open('PUT', sasUrl, true);
    xhr.setRequestHeader('x-ms-blob-type', 'BlockBlob');
    xhr.onload = function () {
        if (xhr.status !== 201) {
            throw new Error('Upload failed.');
        }
    };
    xhr.send(file);
}