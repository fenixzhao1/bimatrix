import {html,PolymerElement} from '/static/otree-redwood/node_modules/@polymer/polymer/polymer-element.js';
// other imports go here

export class ClassName extends PolymerElement {
	constructor() {
		super();
	}

	static get template() {
		return html `
			dom goes here
		`
	}

	static get properties() {
		return {
			// properties go here
		}
	}

    // all other methods go here
	// if a method uses the $$ operator, replace it with shadowRoot.querySelector() for the same effect
	// ready and connectedCallback require super.ready() and super.connectedCallback() respectively

}

window.customElements.define('class-name', ClassName);
