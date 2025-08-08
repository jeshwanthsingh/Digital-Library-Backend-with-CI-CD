<script>
    import InfoPanel from './InfoPanel.svelte';
    import { push } from 'svelte-spa-router';
    
    let fullName = '';
    let email = '';
    let password = '';
    let confirmPassword = '';
    let agreeTerms = false;
    let showPassword = false;
    let showConfirmPassword = false;
    let errorMessage = '';
    let isSubmitting = false;

    // Handle navigation to login page
    function goToLogin() {
    push('/login');
    }

    // Validate SFSU email format
    function validateEmail(email) {
      return email.endsWith('@sfsu.edu') || email.endsWith('@mail.sfsu.edu');
    }
    
    // Toggle password visibility
    function togglePasswordVisibility() {
      showPassword = !showPassword;
    }
    
    function toggleConfirmPasswordVisibility() {
      showConfirmPassword = !showConfirmPassword;
    }
    
    // Form submission handling
    async function handleSubmit() {
      // Reset error message
      errorMessage = '';
      
      // Validation
      if (fullName.trim().length < 2) {
        errorMessage = 'Please enter your full name.';
        return;
      }
      
      // Validate email
      if (!validateEmail(email)) {
        errorMessage = 'Please use your SFSU email address to register.';
        return;
      }
      
      // Check if password is at least 8 characters
      if (password.length < 8) {
        errorMessage = 'Password must be at least 8 characters long.';
        return;
      }
      
      // Check if passwords match
      if (password !== confirmPassword) {
        errorMessage = 'Passwords do not match.';
        return;
      }
      
      // Check terms agreement
      if (!agreeTerms) {
        errorMessage = 'You must agree to the Terms of Service and Privacy Policy.';
        return;
      }
      
      isSubmitting = true;

      try {
        const response = await fetch('http://localhost:8000/api/auth/register', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ username: fullName.trim(), email: email.trim(), password: password }),
        });

        if (response.ok) {
          // Assuming successful registration, redirect to login page
          push('/login');
        } else {
          const errorData = await response.json();
          errorMessage = errorData.detail || 'Registration failed. Please try again.';
        }
      } catch (error) {
        console.error('Registration failed:', error);
        errorMessage = 'An error occurred during registration. Please try again later.';
      } finally {
        isSubmitting = false;
      }
    }
    
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
      "Create a profile to buy and sell items",
      "Access exclusive SFSU student offers",
      "List your services and skills for the community",
      "Secure messaging with verified SFSU members",
      "Free to join - only SFSU emails accepted"
    ];
  </script>
  
  <svelte:head>
    <title>Register - Agora SFSU Marketplace</title>
  </svelte:head>
  
  <main>
    <section class="login-container">
      <div class="login-card">
        <h2>Create Account</h2>
        <p class="subtitle">Join the SFSU community marketplace</p>
        
        {#if errorMessage}
          <div class="error-message" style="display: block;">{errorMessage}</div>
        {/if}
        
        <form on:submit|preventDefault={handleSubmit}>
          <div class="form-group">
            <label for="full-name">Full Name<span class="required-indicator">*</span></label>
            <input
              type="text"
              id="full-name"
              name="full-name"
              required
              placeholder="Your full name"
              bind:value={fullName}
            >
          </div>
          
          <div class="form-group">
            <label for="email">SFSU Email Address<span class="required-indicator">*</span></label>
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
            <label for="password">Password<span class="required-indicator">*</span></label>
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
          
          <div class="form-group">
            <label for="confirm-password">Confirm Password<span class="required-indicator">*</span></label>
            <div class="password-input">
              {#if showConfirmPassword}
              <input
                type="text"
                id="confirm-password"
                name="confirm-password"
                required
                bind:value={confirmPassword}
              >
              {:else}
              <input
                type="password"
                id="confirm-password"
                name="confirm-password"
                required
                bind:value={confirmPassword}
               >
              {/if}
              <button type="button" class="toggle-password" on:click={toggleConfirmPasswordVisibility}>
                <i class="eye-icon">{showConfirmPassword ? '👁️‍🗨️' : '👁️'}</i>
              </button>
            </div>
          </div>
          
          <div class="form-group remember-forgot">
            <div class="remember-me">
              <input type="checkbox" id="terms" name="terms" required bind:checked={agreeTerms}>
              <label for="terms">I agree to the <a href="/terms">Terms of Service</a> and <a href="/privacy">Privacy Policy</a></label>
            </div>
          </div>
          
          <button type="submit" class="btn btn-primary btn-full" disabled={isSubmitting}>
            {isSubmitting ? 'Creating Account...' : 'Create Account'}
          </button>
        </form>
        
        <div class="divider">
          <span>OR</span>
        </div>
        
        <button class="btn btn-sfsu btn-full">
          <img src="sfsu-icon.png" alt="SFSU Icon" class="sfsu-icon">
          Sign up with SFSU
        </button>
        
        <p class="signup-link">
          Already have an account? <a href="/login" on:click|preventDefault={goToLogin}>Log In</a>
        </p>
      </div>
      
      <InfoPanel title="Join Our Community" items={infoItems} />
    </section>
  </main>
  <style>
    /* Google Font Imports */
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap');

/* CSS Variables for theming */
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

.required-indicator {
  color: #D32F2F; /* Your error color variable */
  margin-left: 2px;
}


a {
    text-decoration: none;
    color: var(--primary-color);
    transition: var(--transition);
}

a:hover {
    color: var(--primary-dark);
}

/* Main Container Styles */
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

/* Login Card Styles */
.login-card {
    background-color: var(--card-background);
    border-radius: 12px;
    box-shadow: var(--shadow-lg);
    padding: 40px;
    width: 480px;
    transition: var(--transition);
    position: relative;
    overflow: hidden;
    animation: fadeUp 0.6s ease-out;
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

/* Heading Styles */
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

/* Form Styles */
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

/* Password Input and Toggle */
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

/* Remember Me & Forgot Password */
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

/* Divider */
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

/* Button Styles */
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

/* Signup Link */
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

/* Error Message */
.error-message {
    background-color: rgba(211, 47, 47, 0.1);
    color: var(--error-color);
    padding: 12px 16px;
    border-radius: 8px;
    margin-bottom: 20px;
    display: none;
    font-size: 14px;
    border-left: 4px solid var(--error-color);
    animation: fadeIn 0.3s ease-in-out;
}

/* Validation Styling */
.validation-message {
    color: var(--error-color);
    font-size: 12px;
    margin-top: 6px;
    animation: fadeIn 0.3s ease;
}

.invalid-input {
    border-color: var(--error-color) !important;
}

.invalid-input:focus {
    box-shadow: 0 0 0 3px rgba(211, 47, 47, 0.1) !important;
}

/* Animations */
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(-10px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
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
  </style>