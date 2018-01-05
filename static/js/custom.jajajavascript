var urlField = document.getElementById('urlInput');
var urlButton = document.getElementById('urlButton');
var messageField = document.getElementById('urlInputLabel');

function showErrorMessage(message) {
  messageField.innerHTML = "Error: " + message + ". Sorry :(";
  messageField.style.backgroundColor = '#FF0000';
  setTimeout(function(){
      messageField.innerHTML = "Your URL"
      messageField.style.backgroundColor = '#FFFFFF';
  }, 3000);
}

function forwardToShortUrl(id) {
  var fullDomain = location.protocol + '//' + location.hostname + (location.port ? ':' + location.port: '') + location.pathname;
  if(location.pathname == "/") {
    window.location.href = fullDomain + id;
  } else {
    window.location.href = fullDomain + '/' + id;
  }
}

function getIdForUrl() {
  var r = new XMLHttpRequest();
  if(location.pathname == "/") {
    var destination = location.pathname + "url/";
  } else {
    var destination = location.pathname + "/url/";
  }
  r.open("POST", destination, true);

  r.onreadystatechange = function () {
    if(r.readyState === XMLHttpRequest.DONE && r.status === 200) {
      response = JSON.parse(r.responseText);
      if(response.message == "" || response.message == null) {
        forwardToShortUrl(response.id);
      } else {
        showErrorMessage(response.message);
      }
    } else {
      // showErrorMessage("Please try again later");
      return;
    }
  };

  r.setRequestHeader("X-CSRFToken", csrf_token);
  r.setRequestHeader("Content-type", "application/x-www-form-urlencoded");
  decodedURI = decodeURIComponent(urlField.value);
  r.send("url=" + encodeURIComponent(decodedURI));
  return false;
};

urlButton.onclick = getIdForUrl;

urlField.addEventListener("keydown", function(event) {
    if(event.keyCode == 13) {
        event.preventDefault();
        getIdForUrl();
    }
});
