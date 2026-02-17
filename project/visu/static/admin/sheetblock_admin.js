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

        function toggleFields() {
            var selectedType = typeField.value;
            if (fieldsRow) fieldsRow.style.display = 'none';
            if (extraFieldsRow) extraFieldsRow.style.display = 'none';
            if (textRow) textRow.style.display = 'none';
            if (sourceRow) sourceRow.style.display = 'none';

            // Show relevant fields based on type
            if ((selectedType === 'FIELDS') || (selectedType === 'FIELDS_TABLE') || (selectedType === 'BOOLEANS') || (selectedType === 'BAR_PLOT') || (selectedType === 'DISTRIB_PLOT')) {
                if (fieldsRow) fieldsRow.style.display = '';
                if (fieldsRow) fieldsRow.style.display = '';
            } else if (selectedType === 'TEXT') {
                if (textRow) textRow.style.display = '';
                if (textRow) textRow.style.display = '';
            } else if ((selectedType === 'PANORAMAX') || (selectedType === 'MAP')) {
                if (sourceRow) sourceRow.style.display = '';
                if (sourceRow) sourceRow.style.display = '';
            }
            else if (selectedType === 'RADAR_PLOT') {
                if (fieldsRow) fieldsRow.style.display = '';
                if (fieldsRow) fieldsRow.style.display = '';
                if (extraFieldsRow) extraFieldsRow.style.display = '';
                if (extraFieldsRow) extraFieldsRow.style.display = '';
            }
            // For 'textual', all remain hidden
        }

        toggleFields();

        typeField.addEventListener('change', toggleFields);
    });
})();