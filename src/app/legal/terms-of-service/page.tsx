export default function TermsOfService() {
  return (
    <div className="py-12 lg:py-8">
      <h1 className="text-3xl font-bold mb-6 text-foreground">Terms of Service</h1>

      <div className="prose max-w-none">
        <p className="mb-4">Last updated: {new Date().toLocaleDateString()}</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">1. Acceptance of Terms</h2>
        <p>By accessing and using Pablo (&quot;the Service&quot;), you accept and agree to be bound by the terms and provisions of this agreement. If you do not agree to these terms, do not use the Service.</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">2. Description of Service</h2>
        <p>Pablo provides tools for managing and analyzing social media advertising. The Service is provided &quot;as is&quot; and on an &quot;as available&quot; basis without any representation or warranty, whether express, implied or statutory.</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">3. User Accounts</h2>
        <p>To use certain features of the Service, you must register for an account. You agree to provide accurate, current, and complete information during the registration process and to update such information to keep it accurate, current, and complete.</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">4. User Conduct</h2>
        <p>You agree not to use the Service to:</p>
        <ul className="list-disc pl-5 mb-4">
          <li>Violate any laws or regulations</li>
          <li>Infringe the rights of any third party</li>
          <li>Transmit any material that is unlawful, harmful, threatening, abusive, harassing, defamatory, vulgar, obscene, or otherwise objectionable</li>
          <li>Transmit any unsolicited or unauthorized advertising, promotional materials, spam, or any other form of solicitation</li>
          <li>Transmit any material that contains viruses, Trojan horses, worms, or any other harmful or destructive code</li>
        </ul>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">5. Intellectual Property</h2>
        <p>The Service and its original content, features, and functionality are owned by Pablo and are protected by international copyright, trademark, patent, trade secret, and other intellectual property or proprietary rights laws.</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">6. Termination</h2>
        <p>We may terminate or suspend your account and bar access to the Service immediately, without prior notice or liability, under our sole discretion, for any reason whatsoever and without limitation, including but not limited to a breach of the Terms.</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">7. Limitation of Liability</h2>
        <p>In no event shall Pablo, nor its directors, employees, partners, agents, suppliers, or affiliates, be liable for any indirect, incidental, special, consequential or punitive damages, including without limitation, loss of profits, data, use, goodwill, or other intangible losses, resulting from your access to or use of or inability to access or use the Service.</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">8. Changes to Terms</h2>
        <p>We reserve the right, at our sole discretion, to modify or replace these Terms at any time. If a revision is material we will provide at least 30 days&apos; notice prior to any new terms taking effect. What constitutes a material change will be determined at our sole discretion.</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">9. Contact Us</h2>
        <p>If you have any questions about these Terms, please contact us at:</p>
        <p>Email: hello@pablo.social</p>
      </div>
    </div>
  );
} 