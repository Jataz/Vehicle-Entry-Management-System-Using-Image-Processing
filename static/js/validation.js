$(document).ready(function() {
  $('form').submit(function(event) {
    var name = $('#owner').val();
    var email = $('#email').val();

    if (name.length < 3) {
      $('#owner-error').text('Name must be at least 3 characters long');
      event.preventDefault();
    } else {
      $('#owner-error').text('');
    }

    if (!isValidEmail(email)) {
      $('#email-error').text('Please enter a valid email address');
      event.preventDefault();
    } else {
      $('#email-error').text('');
    }
  });

  function isValidEmail(email) {
    var regex = /\S+@\S+\.\S+/;
    return regex.test(email);
  }
});
