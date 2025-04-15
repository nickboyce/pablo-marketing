import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="w-full bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container mx-auto px-4 flex h-14 items-center max-w-4xl">
        <div className="mr-4">
          <Link href="/" className="mr-6 flex items-center">
            <div className="flex items-center">
              <Image 
                src="/brand/pablo-character.png" 
                alt="Pablo Character" 
                width={40}
                height={40}
                className="h-10 mr-2"
              />
              <Image 
                src="/brand/pablo-logotype.svg" 
                alt="Pablo" 
                width={80}
                height={32}
                className="h-8"
              />
            </div>
          </Link>
        </div>
        <div className="flex flex-1 items-center justify-end space-x-2">
          <nav className="flex items-center space-x-2">
            <Button variant="ghost" asChild>
              <Link href="https://app.pablo.social/auth/login">Login</Link>
            </Button>
          </nav>
        </div>
      </div>
    </header>
  );
} 