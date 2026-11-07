(() => {
    const form = document.getElementById('theme-form');
    const select = document.getElementById('theme-select');
    const status = document.getElementById('theme-status');
    const toggle = document.getElementById('theme-toggle');
    const controlStatus = document.getElementById('theme-control-status');
    if (!form || !select || !status) return;

    const showStatus = (message, shortMessage = message) => {
        status.textContent = message;
        if (controlStatus) controlStatus.textContent = shortMessage;
    };
    const applyTheme = (theme) => {
        document.documentElement.dataset.tema = theme;
        select.value = theme;
        if (toggle) toggle.textContent = theme === 'oscuro' ? 'Modo claro' : 'Modo oscuro';
    };
    const saveTheme = async (theme) => {
        applyTheme(theme);
        if (form.dataset.save !== 'true') {
            showStatus('Tema aplicado a esta página. Acepta las cookies opcionales para guardarlo.', 'Acepta cookies para guardarlo.');
            return;
        }
        const button = form.querySelector('button');
        button.disabled = true;
        if (toggle) toggle.disabled = true;
        try {
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
            });
            if (!response.ok) throw new Error('No se pudo guardar');
            showStatus('Tema guardado en este navegador.', 'Tema guardado.');
        } catch {
            showStatus('Tema aplicado, pero no se pudo guardar. Inténtalo otra vez.', 'No se pudo guardar.');
        } finally {
            button.disabled = false;
            if (toggle) toggle.disabled = false;
        }
    };
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        saveTheme(select.value);
    });
    if (toggle) toggle.addEventListener('click', () => {
        saveTheme(document.documentElement.dataset.tema === 'oscuro' ? 'claro' : 'oscuro');
    });
})();
