import React from 'react';
import { Field as FFField } from 'react-final-form';
import { FormGroup, InputGroup, Intent } from '@blueprintjs/core';

export const Field = ({ label, required, ...props }) => (
  <FFField
    {...props}
    validate={v => (!required || v ? null : 'Le champs est requis')}
    render={({ input, meta }) => (
      <FormGroup
        label={label}
        helperText={meta.touched && meta.error}
        intent={meta.touched && meta.error ? Intent.DANGER : Intent.PRIMARY}
      >
        <InputGroup
          {...input}
        />
      </FormGroup>
    )}
  />
);

export default Field;
