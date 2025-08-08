<script>
  import MessagingWrapper from '../components/messaging/MessagingWrapper.svelte';

  // The router passes route parameters as a 'params' prop
  export let params = {};
</script>

<MessagingWrapper {params} />