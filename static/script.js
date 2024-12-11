document.addEventListener("DOMContentLoaded", function(event) {

    // document elements
    const radioFileInput = document.getElementById("file_upload");
    const radioIdInput = document.getElementById("id_input");
    const submissionIdInput = document.getElementById("submissionId");
    const fileInput = document.getElementById("myfile");

    // select form
    var forms = document.querySelectorAll('.needs-validation');

    Array.prototype.slice.call(forms)
    .forEach(function (form) {
      form.addEventListener('submit', function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }

        // check file type
        if (submissionIdInput.disabled == true && fileInput.disabled == false) {
            fileName = fileInput.value;
            fileType = fileName.split('.').pop();

            // if filetype is wrong
            if (fileType.toLowerCase() != 'csv' && fileName!= '') {
                // display errors to user
                alert(("Please only submit '.csv' filetypes."));

                // stop form submission
                event.preventDefault();
                event.stopPropagation();
            }
        }

        form.classList.add('was-validated');
      }, false)
    });

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
        // disable accordingly
        submissionIdInput.disabled = true;
        fileInput.disabled = false;

        // require accordingly
        submissionIdInput.required = false;
        fileInput.required = true;
    }

    function submissionIdInputSelected() {
        // disable accordingly
        submissionIdInput.disabled = false;
        fileInput.disabled = true;

        // require accordingly
        submissionIdInput.required = true;
        fileInput.required = false;
    }
  });



