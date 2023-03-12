import React from 'react';
import { Form } from 'react-final-form';
import { Button, Toaster, Intent } from '@blueprintjs/core';
import Api from '@terralego/core/modules/Api';
import { withRouter } from 'react-router';

import Field from './Field';

export class FormProfile extends React.Component {
  state = {}

  toasterRefHandler = toaster => { this.toaster = toaster; };

  onSubmit = async data => {
    const { create, history: { replace } } = this.props;

    if (create) {
      const { id, token } = create;
      const { password, password2, ...properties } = data;
      try {
        await Api.request(`accounts/change-password/reset/${id}/${token}/`, {
          method: 'post',
          body: {
            new_password1: password,
            new_password2: password2,
            properties,
          },
        });
        this.toaster.show({
          message: 'Votre inscription a bien été prise en compte. Vous recevrez un email une fois qu\'un administrateur aura validé votre compte.',
          intent: Intent.SUCCESS,
        });
        setTimeout(() => replace('/'), 3000);
      } catch (e) {
        this.toaster.show({
          message: 'Une erreur est survenue. Veuillez réessayer ou contacter le support.',
          intent: Intent.DANGER,
        });
      }
    }
  }

  validate = ({
    password = '',
    password2 = '',
  }) => {
    const errors = {};

    if (password && password.length < 3) {
      errors.password = 'Le mot de passe doit être constituté d\'au moins 3 caractères.';
    }
    if (password !== password2) {
      errors.password2 = 'Les deux mots de passe doivent être identiques.';
    }

    return errors;
  }

  render () {
    const { create } = this.props;

    return (
      <Form
        onSubmit={this.onSubmit}
        validate={this.validate}
        render={({ handleSubmit, pristine, invalid }) => (
          <form onSubmit={handleSubmit} className="profile-form">
            {create && (
              <fieldset className="profile-form__fieldset">
                <p>Bienvenue, veuillez finaliser votre inscription en complétant votre profil :</p>
              </fieldset>
            )}
            <fieldset className="profile-form__fieldset">
              <legend className="profile-form__legend">Définissez un mot de passe</legend>
              <Field
                name="password"
                label="Créez un mot de passe"
                type="password"
                required={!!create}
              />
              <Field
                name="password2"
                label="Vérifiez votre mot de passe"
                type="password"
                required={!!create}
              />
            </fieldset>
            <fieldset className="profile-form__fieldset">
              <legend className="profile-form__legend">Renseignez votre profil</legend>
              <Field
                name="firstname"
                label="Prénom"
                required
              />
              <Field
                name="lastname"
                label="Nom"
                required
              />
              <Field
                name="organization"
                label="Organisme"
                required
              />
              <Field
                name="job"
                label="Poste"
                required
              />
              <Field
                name="service"
                label="Service"
                required
              />
              <Field
                name="phone"
                label="Téléphone"
                required
              />
            </fieldset>
            <fieldset className="profile-form__fieldset">
              <Button
                type="submit"
                disabled={pristine || invalid}
              >
                Enregistrer
              </Button>
            </fieldset>
            <Toaster
              className="profile-form__toaster"
              ref={this.toasterRefHandler}
              canEscapeKeyClear
            />
          </form>
        )}
      />
    );
  }
}

export default withRouter(FormProfile);
