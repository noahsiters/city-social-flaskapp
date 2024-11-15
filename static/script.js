document.addEventListener("DOMContentLoaded", function(event) {

    // document elements
    const radioFileInput = document.getElementById("file_upload");
    const radioIdInput = document.getElementById("id_input");
    const submissionIdInput = document.getElementById("submissionId")
    const fileInput = document.getElementById("myfile")

    // on load
    window.onload = function() {
        if (radioFileInput.checked) {
            fileInputSelected();
        }
        else if (radioIdInput.checked) {
            submissionIdInputSelected();
        }
    }
;
    // click events
    radioFileInput.addEventListener("click", function(event) {
        fileInputSelected();
    });
    radioIdInput.addEventListener("click", function(event) {
        submissionIdInputSelected();
    });

    // functions
    function fileInputSelected() {
        submissionIdInput.disabled = true;
        fileInput.disabled = false;
    }

    function submissionIdInputSelected() {
        submissionIdInput.disabled = false;
        fileInput.disabled = true;
    }
  });



