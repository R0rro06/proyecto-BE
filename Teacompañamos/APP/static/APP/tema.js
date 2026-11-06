(() => {
    const form = document.getElementById('theme-form');
    const select = document.getElementById('theme-select');
    const status = document.getElementById('theme-status');
    form.addEventListener('submit', async (event) => {
        event.preventDefault();
        document.documentElement.dataset.tema = select.value;
        if (form.dataset.save !== 'true') {
            status.textContent = 'Tema aplicado a esta página. Acepta las cookies opcionales para guardarlo.';
            return;
        }
        const button = form.querySelector('button');
        button.disabled = true;
        try {
            const response = await fetch(form.action, {
                method: 'POST', body: new FormData(form), credentials: 'same-origin',
            });
            if (!response.ok) throw new Error('No se pudo guardar');
            status.textContent = 'Tema guardado en este navegador.';
        } catch {
            status.textContent = 'Tema aplicado, pero no se pudo guardar. Inténtalo otra vez.';
        } finally {
            button.disabled = false;
        }
    });
})();
