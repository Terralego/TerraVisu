(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var typeField = document.getElementById('id_type');

        if (!typeField) {
            return;
        }

        var pictoTrueRow = document.querySelector('.field-picto_true');
        var pictoFalseRow = document.querySelector('.field-picto_false');
        var suffixRow = document.querySelector('.field-suffix');
        var decimalsRow = document.querySelector('.field-decimals');

        function toggleFields() {
            var selectedType = typeField.value;
            if (pictoTrueRow) pictoTrueRow.style.display = 'none';
            if (pictoFalseRow) pictoFalseRow.style.display = 'none';
            if (suffixRow) suffixRow.style.display = 'none';
            if (decimalsRow) decimalsRow.style.display = 'none';

            // Show relevant fields based on type
            if (selectedType === 'BOOLEAN') {
                if (pictoTrueRow) pictoTrueRow.style.display = '';
                if (pictoFalseRow) pictoFalseRow.style.display = '';
            } else if (selectedType === 'NUMERICAL') {
                if (suffixRow) suffixRow.style.display = '';
                if (decimalsRow) decimalsRow.style.display = '';
            }
            // For 'textual', all remain hidden
        }

        toggleFields();

        typeField.addEventListener('change', toggleFields);
    });
})();