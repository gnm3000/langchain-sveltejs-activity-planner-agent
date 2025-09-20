<script>
    import { marked } from 'marked';

    let city = '';

    /** @type {{ greeting: string; city: string; plan: string } | null} */
    let data = null;

    let loading = false;

    /** @type {string | null} */
    let error = null;

    async function fetchActivity() {
        if (!city.trim()) return;

        loading = true;
        error = null;
        data = null;

        try {
            const response = await fetch(`http://localhost:8000/get-activity?city=${encodeURIComponent(city)}`);
            if (!response.ok) {
                throw new Error(`Error: ${response.statusText}`);
            }
            data = await response.json();
        } catch (err) {
            error = err.message;
        } finally {
            loading = false;
        }
    }

    function renderMarkdown(text) {
        return marked(text || '');
    }
</script>

<h1>Activity Planner</h1>

<div>
    <input 
        type="text" 
        placeholder="Enter city name" 
        bind:value={city} 
    />
    <button on:click={fetchActivity}>Get Activity Plan</button>
</div>

{#if loading}
    <p>Loading...</p>
{/if}

{#if error}
    <p style="color: red;">Error: {error}</p>
{/if}

{#if data}
    <div class="result">
        <h2>{data.greeting}</h2>
        <p><strong>City:</strong> {data.city}</p>
        <div class="markdown">
    {@html renderMarkdown(data.plan)}
</div>
    </div>
{/if}

<style>
    h1 {
        font-size: 2rem;
        margin-bottom: 1rem;
    }

    input {
        padding: 0.5rem;
        margin-right: 0.5rem;
        border: 1px solid #ccc;
        border-radius: 4px;
    }

    button {
        padding: 0.5rem 1rem;
        background: #333;
        color: white;
        border: none;
        border-radius: 4px;
        cursor: pointer;
    }

    button:hover {
        background: #555;
    }

    .result {
        margin-top: 1.5rem;
        padding: 1rem;
        border: 1px solid #ddd;
        border-radius: 4px;
        background: #f9f9f9;
    }

    .markdown {
        margin-top: 1rem;
        line-height: 1.6;
    }

    .markdown strong {
        font-weight: bold;
    }

    .markdown ul {
        padding-left: 1.2rem;
        list-style-type: disc;
    }

    .markdown h1,
    .markdown h2,
    .markdown h3 {
        margin-top: 1rem;
    }
</style>
