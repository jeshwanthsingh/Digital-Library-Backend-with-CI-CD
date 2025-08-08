<script>
  import { push } from 'svelte-spa-router'; // Import push

  let email = '';
  let message = '';
  let isSubmitting = false;

  async function handleSubmit() {
    isSubmitting = true;
    message = '';

    if (!email.trim()) {
      message = 'Please enter your SFSU email address.';
      isSubmitting = false;
      return;
    }

    // For admin-assisted reset, we don't need to simulate an API call here.
    // We just display a message.
    console.log(`Password reset assistance requested for: ${email}`);
    
    message = `Password reset for SFSU accounts requires administrator assistance. Please contact an administrator with your SFSU email address ('${email}') to request a password reset.`;
    // In a real scenario, you might log this request or provide a specific admin contact.
    
    isSubmitting = false;
    // email = ''; // Optionally clear email field
  }

  function goToLogin() {
    push('/login');
  }
</script>

<svelte:head>
  <title>Forgot Password - Agora SFSU Marketplace</title>
</svelte:head>

<main class="forgot-password-container">
  <div class="forgot-password-card">
    <h2>Forgot Your Password?</h2>
    <p class="subtitle">Enter your SFSU email address below, and if an account exists, we'll (eventually) send you a link to reset your password.</p>

    {#if message}
      <div class="message" role="alert">{message}</div>
    {/if}

    <form on:submit|preventDefault={handleSubmit}>
      <div class="form-group">
        <label for="email">SFSU Email Address</label>
        <input
          type="email"
          id="email"
          name="email"
          required
          placeholder="youremail@sfsu.edu"
          bind:value={email}
          disabled={isSubmitting}
        />
      </div>

      <button type="submit" class="btn btn-primary btn-full" disabled={isSubmitting}>
        {isSubmitting ? 'Processing...' : 'Send Reset Link'}
      </button>
    </form>

    <p class="login-link">
      Remember your password? <a href="/login" on:click|preventDefault={goToLogin}>Log In</a>
    </p>
  </div>
</main>

<style>
  .forgot-password-container { display: flex; justify-content: center; align-items: center; padding: 40px 20px; font-family: 'Roboto', sans-serif; }
  .forgot-password-card { background-color: #fff; border-radius: 12px; box-shadow: 0 8px 24px rgba(94, 53, 177, 0.15); padding: 40px; width: 100%; max-width: 480px; text-align: center; }
  h2 { color: #5E35B1; margin-bottom: 10px; font-size: 28px; }
  .subtitle { color: #757575; margin-bottom: 30px; font-size: 16px; }
  .form-group { margin-bottom: 24px; text-align: left; }
  label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
  input[type="email"] { width: 100%; padding: 14px 16px; border: 2px solid #E0E0E0; border-radius: 8px; font-size: 16px; background-color: #f9fafb; }
  input[type="email"]:focus { border-color: #5E35B1; outline: none; box-shadow: 0 0 0 3px rgba(94, 53, 177, 0.1); }
  .btn { display: inline-block; padding: 12px 24px; border-radius: 6px; font-weight: 600; font-size: 15px; cursor: pointer; border: none; text-align: center; }
  .btn-primary { background: linear-gradient(135deg, #5E35B1, #4527A0); color: white; box-shadow: 0 4px 10px rgba(94, 53, 177, 0.3); }
  .btn-full { width: 100%; margin: 16px 0; }
  .message { margin-bottom: 20px; padding: 10px; border-radius: 6px; background-color: #e3f2fd; color: #0d47a1; border: 1px solid #90caf9; }
  .login-link { margin-top: 20px; font-size: 14px; }
  .login-link a { color: #5E35B1; font-weight: 500; }
</style>