(function() {
    'use strict';

    document.addEventListener('DOMContentLoaded', function() {
        var typeField = document.getElementById('id_type');

        if (!typeField) {
            return;
        }

        var fieldsRow = document.querySelector('#sheetfieldthroughmodel_set-group');
        var extraFieldsRow = document.querySelector('#extrasheetfieldthroughmodel_set-group');
        var textRow = document.querySelector('.field-text');
        var sourceRow = document.querySelector('.field-source');
        var orderRow = document.querySelector('.field-order_field');
        var limitRow = document.querySelector('.field-limit');

        function toggleFields() {
            var selectedType = typeField.value;
            if (fieldsRow) fieldsRow.style.display = 'none';
            if (extraFieldsRow) extraFieldsRow.style.display = 'none';
            if (textRow) textRow.style.display = 'none';
            if (sourceRow) sourceRow.style.display = 'none';
            if (orderRow) orderRow.style.display = 'none';
            if (limitRow) limitRow.style.display = 'none';

            // Show relevant fields based on type
            if ((selectedType === 'FIELDS') || (selectedType === 'BOOLEANS') || (selectedType === 'BAR_PLOT') || (selectedType === 'DISTRIB_PLOT')) {
                if (fieldsRow) fieldsRow.style.display = '';
            } else if (selectedType === 'TEXT') {
                if (textRow) textRow.style.display = '';
            } else if ((selectedType === 'PANORAMAX') || (selectedType === 'MAP')) {
                if (sourceRow) sourceRow.style.display = '';
            } else if (selectedType === 'FIELDS_TABLE') {
                if (fieldsRow) fieldsRow.style.display = '';
                if (orderRow) orderRow.style.display = '';
                if (limitRow) limitRow.style.display = '';
            } else if (selectedType === 'RADAR_PLOT') {
                if (fieldsRow) fieldsRow.style.display = '';
                if (extraFieldsRow) extraFieldsRow.style.display = '';
            }
            // For 'textual', all remain hidden
        }

        toggleFields();

        typeField.addEventListener('change', toggleFields);
    });
})();