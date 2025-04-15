export default function PrivacyPolicy() {
  return (
    <div className="py-12 lg:py-8">
      <h1 className="text-3xl font-bold mb-6 text-foreground">Privacy Policy</h1>

      <div className="prose max-w-none">
        <p className="mb-4">Last updated: {new Date().toLocaleDateString()}</p>
        
        <h2 className="text-xl font-semibold mt-6 mb-3">1. Introduction</h2>
        <p>Welcome to Pablo (&quot;we,&quot; &quot;our,&quot; or &quot;us&quot;). We respect your privacy and are committed to protecting your personal data. This privacy policy will inform you about how we look after your personal data when you visit our website and tell you about your privacy rights and how the law protects you.</p>
        
        <h2 className="text-2xl mt-6 mb-3">2. Data We Collect</h2>
        <p>We may collect, use, store and transfer different kinds of personal data about you which we have grouped together as follows:</p>
        <ul className="list-disc pl-5 mb-4">
          <li>Identity Data: includes first name, last name, username or similar identifier</li>
          <li>Contact Data: includes email address</li>
          <li>Technical Data: includes internet protocol (IP) address, browser type and version, time zone setting and location, browser plug-in types and versions, operating system and platform</li>
          <li>Usage Data: includes information about how you use our website and services</li>
        </ul>
        
        <h2 className="text-2xl mt-6 mb-3">3. How We Use Your Data</h2>
        <p>We will only use your personal data when the law allows us to. Most commonly, we will use your personal data in the following circumstances:</p>
        <ul className="list-disc pl-5 mb-4">
          <li>To register you as a new customer</li>
          <li>To provide and manage your account</li>
          <li>To provide our services to you</li>
          <li>To manage our relationship with you</li>
          <li>To improve our website, products/services, marketing or customer relationships</li>
        </ul>
        
        <h2 className="text-2xl mt-6 mb-3">4. Data Sharing</h2>
        <p>We may share your personal data with the parties set out below:</p>
        <ul className="list-disc pl-5 mb-4">
          <li>Service providers who provide IT and system administration services</li>
          <li>Professional advisers including lawyers, bankers, auditors and insurers</li>
          <li>Regulators and other authorities who require reporting of processing activities in certain circumstances</li>
        </ul>
        
        <h2 className="text-2xl mt-6 mb-3">5. Data Security</h2>
        <p>We have put in place appropriate security measures to prevent your personal data from being accidentally lost, used or accessed in an unauthorized way, altered or disclosed.</p>
        
        <h2 className="text-2xl mt-6 mb-3">6. Data Retention</h2>
        <p>We will only retain your personal data for as long as necessary to fulfill the purposes we collected it for, including for the purposes of satisfying any legal, accounting, or reporting requirements.</p>
        
        <h2 className="text-2xl mt-6 mb-3">7. Your Legal Rights</h2>
        <p>Under certain circumstances, you have rights under data protection laws in relation to your personal data, including the right to:</p>
        <ul className="list-disc pl-5 mb-4">
          <li>Request access to your personal data</li>
          <li>Request correction of your personal data</li>
          <li>Request erasure of your personal data</li>
          <li>Object to processing of your personal data</li>
          <li>Request restriction of processing your personal data</li>
          <li>Request transfer of your personal data</li>
          <li>Right to withdraw consent</li>
        </ul>
        
        <h2 className="text-2xl mt-6 mb-3">8. Contact Us</h2>
        <p>If you have any questions about this privacy policy or our privacy practices, please contact us at:</p>
        <p>Email: hello@pablo.social</p>
      </div>
    </div>
  );
} 