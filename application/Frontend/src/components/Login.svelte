<script>
    import InfoPanel from './InfoPanel.svelte';
    import { push } from 'svelte-spa-router';
    import { setAuthenticated, setUser } from '../stores/authStore.js'; // Import auth store setters
   
   let email = '';
   let password = '';
    let showPassword = false;
    let rememberMe = false;
    let errorMessage = '';
    let isSubmitting = false;

    // Handle navigation to register page
    function goToRegister() {
        push('/register');
    }

    function goToForgotPassword() {
        push('/forgot-password');
    }
    
    // Check localStorage for remembered email on component mount
    import { onMount } from 'svelte';
    
    onMount(() => {
      if (localStorage.getItem('remember_me') === 'true') {
        const savedEmail = localStorage.getItem('user_email');
        if (savedEmail) {
          email = savedEmail;
          rememberMe = true;
        }
      }
    });
    
    // Validate SFSU email format
    function validateEmail(email) {
      return email.endsWith('@sfsu.edu') || email.endsWith('@mail.sfsu.edu');
    }
    
    // Toggle password visibility
    function togglePasswordVisibility() {
      showPassword = !showPassword;
    }
    
    // Form submission handling
    async function handleSubmit() {
      // Reset error message
      errorMessage = '';

      // Simple validation
      if (!validateEmail(email)) {
          errorMessage = 'Please use your SFSU email address to login.';
          return;
      }

      // Check if password is at least 8 characters
      if (password.length < 8) {
          errorMessage = 'Password must be at least 8 characters long.';
          return;
      }

      // Store or clear credentials based on remember me checkbox
      if (rememberMe) {
          localStorage.setItem('remember_me', 'true');
          localStorage.setItem('user_email', email.trim());
      } else {
          localStorage.removeItem('remember_me');
          localStorage.removeItem('user_email');
      }

      isSubmitting = true;

      try {
          const response = await fetch('/api/auth/login', { // Changed to relative path
              method: 'POST',
              headers: {
                  'Content-Type': 'application/json',
              },
              body: JSON.stringify({ email: email.trim(), password: password }),
          });

          if (response.ok) {
              const data = await response.json();
              // Assuming the backend returns an access_token on successful login
              localStorage.setItem('access_token', data.access_token);
              setAuthenticated(true); // Update the auth store

              // Fetch user details after successful login
              const userResponse = await fetch('/api/auth/me', { // Changed to relative path
                  headers: {
                      'Authorization': `Bearer ${data.access_token}`
                  }
              });

              if (userResponse.ok) {
                  const userData = await userResponse.json();
                  // Combine user data with the access token
                  const userWithToken = { ...userData, token: data.access_token };
                  setUser(userWithToken); // Set the user store with token included
                  console.log('User logged in and user data fetched:', userWithToken);
                  // Redirect to dashboard or desired page after successful login
                  push('/'); // Use svelte-spa-router push for navigation
              } else {
                  // Handle error fetching user data
                  console.error('Failed to fetch user data after login:', userResponse.statusText);
                  errorMessage = 'Login successful, but failed to fetch user data.';
                  // Optionally clear token and auth state if user data fetch fails
                  localStorage.removeItem('access_token');
                  setAuthenticated(false);
                  setUser(null);
              }
          } else {
              const errorData = await response.json();
              errorMessage = errorData.detail || 'Invalid email or password. Please try again.';
          }
      } catch (error) {
          console.error('Login failed:', error);
          errorMessage = 'An error occurred during login. Please try again later.';
      } finally {
          isSubmitting = false;
      }
    }
    // Removed duplicated catch and finally blocks and extra brace
    // } catch (error) { ... } finally { ... } }
    
    // For email validation on blur
    let emailInvalid = false;
    let emailValidationMessage = '';
    
    function validateEmailField() {
      if (email && !validateEmail(email)) {
        emailInvalid = true;
        emailValidationMessage = 'Please use your SFSU email address.';
      } else {
        emailInvalid = false;
        emailValidationMessage = '';
      }
    }
    
    const infoItems = [
      "Exclusive SFSU community marketplace",
      "Buy and sell textbooks, electronics, and more",
      "Find tutors and skill-sharing services",
      "Safe on-campus exchanges",
      "Connect with fellow SFSU students"
    ];
  </script>
  
  <svelte:head>
    <title>Login - Agora SFSU Marketplace</title>
  </svelte:head>
  
  <main>
    <section class="login-container">
      <div class="login-card">
        <h2>Welcome Back</h2>
        <p class="subtitle">Sign in to access the SFSU marketplace</p>
        
        {#if errorMessage}
          <div class="error-message" style="display: block;">{errorMessage}</div>
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
              on:blur={validateEmailField}
              class:invalid-input={emailInvalid}
            >
            {#if emailInvalid}
              <p class="validation-message">{emailValidationMessage}</p>
            {/if}
          </div>
          
          <div class="form-group">
            <label for="password">Password</label>
            <div class="password-input">
              {#if showPassword}
                <input
                  type="text"
                  id="password"
                  name="password"
                  required
                  bind:value={password}
                >
              {:else}
                <input
                  type="password"
                  id="password"
                  name="password"
                  required
                  bind:value={password}
                >
              {/if}
              <button type="button" class="toggle-password" on:click={togglePasswordVisibility}>
                <i class="eye-icon">{showPassword ? '👁️‍🗨️' : '👁️'}</i>
              </button>
            </div>
          </div>
          
          <div class="form-group remember-forgot">
            <div class="remember-me">
              <input type="checkbox" id="remember" name="remember" bind:checked={rememberMe}>
              <label for="remember">Remember me</label>
            </div>
            <a href="/forgot-password" class="forgot-password" on:click|preventDefault={goToForgotPassword}>Forgot Password?</a>
          </div>
          
          <button type="submit" class="btn btn-primary btn-full" disabled={isSubmitting}>
            {isSubmitting ? 'Logging in...' : 'Log In'}
          </button>
        </form>
        
        
        <p class="signup-link">
          Don't have an account? <a href="/register" on:click|preventDefault={goToRegister}>Create Account</a>
        </p>
      </div>
      
      <InfoPanel title="Why Join Agora?" items={infoItems} />
    </section>
  </main>
  <style>
    /* Google Font Import */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

/* CSS Variables for easy theming */
:root {
    --primary-color: #5E35B1;
    --primary-light: #7e57c2;
    --primary-dark: #4527A0;
    --secondary-color: #FFC107;
    --secondary-light: #FFD54F;
    --text-color: #333333;
    --text-light: #757575;
    --background-color: #f8f9fa;
    --card-background: #FFFFFF;
    --border-color: #E0E0E0;
    --error-color: #D32F2F;
    --success-color: #388E3C;
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
    --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.1);
    --shadow-lg: 0 8px 24px rgba(94, 53, 177, 0.15);
    --transition: all 0.3s ease;
}

/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}


a {
    text-decoration: none;
    color: var(--primary-color);
    transition: var(--transition);
}

a:hover {
    color: var(--primary-dark);
}

/* Enhanced Button Styles */
.btn {
    display: inline-block;
    padding: 12px 24px;
    border-radius: 6px;
    font-weight: 600;
    font-size: 15px;
    cursor: pointer;
    transition: var(--transition);
    border: none;
    text-align: center;
    letter-spacing: 0.5px;
    position: relative;
    overflow: hidden;
}

.btn:before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    transition: 0.5s;
}

.btn:hover:before {
    left: 100%;
}

.btn-primary {
    background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
    color: white;
    box-shadow: 0 4px 10px rgba(94, 53, 177, 0.3);
}

.btn-primary:hover {
    background: linear-gradient(135deg, var(--primary-dark), var(--primary-color));
    box-shadow: 0 6px 15px rgba(94, 53, 177, 0.4);
    transform: translateY(-2px);
}

.btn-sfsu {
    background: linear-gradient(135deg, #212121, #000000);
    color: white;
    display: flex;
    justify-content: center;
    align-items: center;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}

.btn-sfsu:hover {
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.25);
    transform: translateY(-2px);
}

.btn-full {
    width: 100%;
    margin: 16px 0;
}

.sfsu-icon {
    width: 20px;
    height: 20px;
    margin-right: 12px;
    transition: var(--transition);
}

/* Enhanced Login Container Styles */
main {
    flex: 1;
    padding: 40px 20px;
}

.login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 40px;
    max-width: 1100px;
    margin: 20px auto;
    padding: 20px;
    position: relative;
}

.login-card {
    background-color: var(--card-background);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
    padding: 40px;
    width: 480px;
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}

.login-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 6px;
    background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
}

.login-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 12px 30px rgba(94, 53, 177, 0.2);
}

h2 {
    color: var(--primary-color);
    margin-bottom: 10px;
    font-size: 32px;
    font-weight: 700;
    position: relative;
    display: inline-block;
}

h2::after {
    content: '';
    position: absolute;
    bottom: -5px;
    left: 0;
    width: 40px;
    height: 3px;
    background-color: var(--secondary-color);
}

.subtitle {
    color: var(--text-light);
    margin-bottom: 30px;
    font-size: 16px;
}

/* Enhanced Form Styles */
.form-group {
    margin-bottom: 24px;
    position: relative;
}

label {
    display: block;
    margin-bottom: 8px;
    font-weight: 500;
    color: var(--text-color);
    font-size: 15px;
    transition: var(--transition);
}

input[type="email"],
input[type="password"],
input[type="text"] {
    width: 100%;
    padding: 14px 16px;
    border: 2px solid var(--border-color);
    border-radius: 8px;
    font-size: 16px;
    transition: var(--transition);
    background-color: #f9fafb;
    color: var(--text-color);
}

input[type="email"]:focus,
input[type="password"]:focus,
input[type="text"]:focus {
    border-color: var(--primary-color);
    outline: none;
    box-shadow: 0 0 0 3px rgba(94, 53, 177, 0.1);
    background-color: white;
}

.password-input {
    position: relative;
}

.toggle-password {
    position: absolute;
    right: 12px;
    top: 50%;
    transform: translateY(-50%);
    background: none;
    border: none;
    cursor: pointer;
    color: var(--text-light);
    transition: var(--transition);
    padding: 5px;
}

.toggle-password:hover {
    color: var(--primary-color);
}

.eye-icon {
    font-size: 18px;
}

.remember-forgot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 5px;
}

.remember-me {
    display: flex;
    align-items: center;
}

.remember-me input[type="checkbox"] {
    appearance: none;
    -webkit-appearance: none;
    width: 18px;
    height: 18px;
    border: 2px solid var(--border-color);
    border-radius: 4px;
    margin-right: 8px;
    position: relative;
    cursor: pointer;
    transition: var(--transition);
}

.remember-me input[type="checkbox"]:checked {
    background-color: var(--primary-color);
    border-color: var(--primary-color);
}

.remember-me input[type="checkbox"]:checked::after {
    content: "✓";
    color: white;
    position: absolute;
    font-size: 12px;
    top: 0;
    left: 4px;
}

.remember-me label {
    margin-bottom: 0;
    font-size: 14px;
    cursor: pointer;
}

.forgot-password {
    font-size: 14px;
    color: var(--primary-color);
    transition: var(--transition);
}

.forgot-password:hover {
    color: var(--primary-dark);
    text-decoration: underline;
}

.divider {
    display: flex;
    align-items: center;
    margin: 24px 0;
}

.divider::before,
.divider::after {
    content: "";
    flex: 1;
    border-bottom: 1px solid var(--border-color);
}

.divider span {
    padding: 0 16px;
    color: var(--text-light);
    font-size: 14px;
    font-weight: 500;
}

.signup-link {
    text-align: center;
    margin-top: 30px;
    font-size: 15px;
}

.signup-link a {
    font-weight: 600;
    color: var(--primary-color);
}

.signup-link a:hover {
    text-decoration: underline;
}

/* Info Panel is imported as component */
/* Keeping these styles in case they're used by InfoPanel.svelte */

.error-message {
    background-color: rgba(211, 47, 47, 0.1);
    color: var(--error-color);
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    font-size: 14px;
    border-left: 4px solid var(--error-color);
    animation: fadeIn 0.3s ease-in-out;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

/* Validation Message Styles */
.validation-message {
    color: var(--error-color);
    font-size: 12px;
    margin-top: 6px;
    animation: fadeIn 0.3s ease;
}

/* Invalid Input Styles */
.invalid-input {
    border-color: var(--error-color) !important;
}

.invalid-input:focus {
    box-shadow: 0 0 0 3px rgba(211, 47, 47, 0.1) !important;
}

/* Responsive Styles */
@media screen and (max-width: 1100px) {
    .login-container {
        max-width: 900px;
        gap: 30px;
    }
    
    .login-card {
        width: 450px;
    }
}

@media screen and (max-width: 900px) {
    .login-container {
        flex-direction: column;
        align-items: stretch;
    }
    
    .login-card {
        width: 100%;
        max-width: 550px;
        margin: 0 auto;
    }
}

@media screen and (max-width: 600px) {
    .login-card {
        padding: 30px 20px;
    }
    
    h2 {
        font-size: 28px;
    }
    
    .btn {
        padding: 12px 20px;
        font-size: 14px;
    }
}

/* Animations */
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(94, 53, 177, 0.4); }
    70% { box-shadow: 0 0 0 10px rgba(94, 53, 177, 0); }
    100% { box-shadow: 0 0 0 0 rgba(94, 53, 177, 0); }
}

.login-card {
    animation: fadeUp 0.6s ease-out;
}

.btn-primary:focus {
    animation: pulse 1.5s infinite;
}
  </style>