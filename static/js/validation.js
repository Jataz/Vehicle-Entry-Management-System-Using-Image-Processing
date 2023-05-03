$(document).ready(function() {
    $('form').submit(function(event) {
      var name = $('#name').val();
      var email = $('#email').val();
  
      if (name.length < 3) {
        alert('Name must be at least 3 characters long');
        event.preventDefault();
      }
  
      if (!isValidEmail(email)) {
        alert('Please enter a valid email address');
        event.preventDefault();
      }
    });
  
    function isValidEmail(email) {
      var regex = /\S+@\S+\.\S+/;
      return regex.test(email);
    }
  });
  