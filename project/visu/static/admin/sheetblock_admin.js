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
        var fieldsSourceRow = document.querySelector('.field-fields_source');
        var firstGeomSourceRow = document.querySelector('.field-first_geom_source');
        var secondGeomSourceRow = document.querySelector('.field-second_geom_source');
        var orderRow = document.querySelector('.field-order_field');
        var limitRow = document.querySelector('.field-limit');

        function toggleFields() {
            var selectedType = typeField.value;
            if (fieldsRow) fieldsRow.style.display = 'none';
            if (extraFieldsRow) extraFieldsRow.style.display = 'none';
            if (textRow) textRow.style.display = 'none';
            if (fieldsSourceRow) fieldsSourceRow.style.display = 'none';
            if (firstGeomSourceRow) firstGeomSourceRow.style.display = 'none';
            if (secondGeomSourceRow) secondGeomSourceRow.style.display = 'none';
            if (orderRow) orderRow.style.display = 'none';
            if (limitRow) limitRow.style.display = 'none';

            // Show relevant fields based on type
            if ((selectedType === 'FIELDS') || (selectedType === 'BOOLEANS') || (selectedType === 'BAR_PLOT') || (selectedType === 'DISTRIB_PLOT')) {
                if (fieldsSourceRow) fieldsSourceRow.style.display = '';
                if (fieldsRow) fieldsRow.style.display = '';
            } else if (selectedType === 'TEXT') {
                if (textRow) textRow.style.display = '';
            } else if (selectedType === 'PANORAMAX') {
                if (firstGeomSourceRow) firstGeomSourceRow.style.display = '';
            } else if (selectedType === 'MAP') {
                if (firstGeomSourceRow) firstGeomSourceRow.style.display = '';
                if (secondGeomSourceRow) secondGeomSourceRow.style.display = '';
            } else if (selectedType === 'FIELDS_TABLE') {
                if (fieldsSourceRow) fieldsSourceRow.style.display = '';
                if (fieldsRow) fieldsRow.style.display = '';
                if (orderRow) orderRow.style.display = '';
                if (limitRow) limitRow.style.display = '';
            } else if (selectedType === 'RADAR_PLOT') {
                if (fieldsSourceRow) fieldsSourceRow.style.display = '';
                if (fieldsRow) fieldsRow.style.display = '';
                if (extraFieldsRow) extraFieldsRow.style.display = '';
            }
            // For 'textual', all remain hidden
        }

        toggleFields();

        typeField.addEventListener('change', toggleFields);
    });
})();