// Global site JavaScript for GameStore
// This file contains all custom JS previously inlined in templates.

(function(){
  // Checkout page: toggle card fields depending on selected payment method
  function initCheckoutToggle(){
    var pmCard = document.getElementById('pm_card');
    var pmPaypal = document.getElementById('pm_paypal');
    var cardFields = document.getElementById('cardFields');
    if (!pmCard || !pmPaypal || !cardFields) return; // Not on checkout page

    function toggleCardFields(){
      if (pmCard.checked) {
        cardFields.style.display = '';
      } else {
        cardFields.style.display = 'none';
      }
    }
    pmCard.addEventListener('change', toggleCardFields);
    pmPaypal.addEventListener('change', toggleCardFields);
    toggleCardFields();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCheckoutToggle);
  } else {
    initCheckoutToggle();
  }
})();
